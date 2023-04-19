import logging
from typing import List

from genologics.entities import Container, Containertype, Project, Researcher, Sample
from lxml import etree
from lxml.objectify import ObjectifiedElement

from cg.constants.lims import PROP2UDF, YES_NO_LIMS_BOOLEANS
from cg.exc import OrderError

from . import batch

LOG = logging.getLogger(__name__)
CONTAINER_TYPE_MAP = {"Tube": 2, "96 well plate": 1}


class OrderHandler:
    def save_xml(self, uri: str, document: ObjectifiedElement):
        """Post the data to the server."""
        data = etree.tostring(document, xml_declaration=True)
        result = self.post(uri, data)
        return result

    def save_containers(self, container_details: ObjectifiedElement):
        """Save a batch of containers."""
        container_uri = f"{self.get_uri()}/containers/batch/create"
        results = self.save_xml(container_uri, container_details)
        container_map = {}
        for link in results.findall("link"):
            lims_container = Container(self, uri=link.attrib["uri"])
            container_map[lims_container.name] = lims_container
        return container_map

    def save_samples(self, sample_details: ObjectifiedElement, map_samples=False):
        """Save a batch of samples."""
        sample_uri = f"{self.get_uri()}/samples/batch/create"
        results = self.save_xml(sample_uri, sample_details)
        if map_samples:
            sample_map = {}
            for link in results.findall("link"):
                lims_sample = Sample(self, uri=link.attrib["uri"])
                sample_map[lims_sample.name] = lims_sample
            return sample_map
        return results

    def update_artifacts(self, artifact_details: ObjectifiedElement):
        """Update/put a batch of artifacts."""
        artifact_uri = f"{self.get_uri()}/artifacts/batch/update"
        results = self.save_xml(artifact_uri, artifact_details)
        return results

    def submit_project(self, project_name: str, samples: List[dict], researcher_id: str = "3"):
        """Parse Scout project."""
        containers = self.prepare(samples)

        lims_project = Project.create(
            self, researcher=Researcher(self, id=researcher_id), name=project_name
        )
        LOG.info("%s: created new LIMS project", lims_project.id)

        containers_data = [
            batch.build_container(
                name=container["name"], con_type=Containertype(lims=self, id=container["type"])
            )
            for container in containers
        ]
        container_details = batch.build_container_batch(containers_data)
        LOG.debug("%s: saving containers", lims_project.name)
        container_map = self.save_containers(container_details)

        reagentlabel_samples = [
            sample
            for container in containers
            for sample in container["samples"]
            if sample["index_sequence"]
        ]

        samples_data = []
        for container in containers:
            for sample in container["samples"]:
                LOG.debug("%s: adding sample to container: %s", sample["name"], container["name"])
                lims_container = container_map[container["name"]]
                sample_data = batch.build_sample(
                    name=sample["name"],
                    project=lims_project,
                    container=lims_container,
                    location=sample["location"],
                    udfs=sample["udfs"],
                )
                samples_data.append(sample_data)
        sample_details = batch.build_sample_batch(samples_data)
        process_reagentlabels = len(reagentlabel_samples) > 0
        sample_map = self.save_samples(sample_details, map_samples=process_reagentlabels)

        if process_reagentlabels:
            artifacts_data = [
                batch.build_artifact(
                    artifact=sample_map[sample["name"]].artifact,
                    reagent_label=sample["index_sequence"],
                )
                for sample in reagentlabel_samples
            ]
            artifact_details = batch.build_artifact_batch(artifacts_data)
            self.update_artifacts(artifact_details)

        lims_project_data = self._export_project(lims_project)
        return lims_project_data

    @classmethod
    def prepare(cls, samples):
        """Convert API input to LIMS input data."""
        lims_containers = []
        tubes, plates, no_container = cls.group_containers(samples)
        # "96 well plate" = container type "1"; Tube = container type "2"; "No container" = container type "3"
        for container_type, containers in [("1", plates), ("2", tubes), ("3", no_container)]:
            for container_name, samples in containers.items():
                new_container = {"name": container_name, "type": container_type, "samples": []}
                # check that positions in plate are unique
                well_positions = {}
                for sample_data in samples:
                    location = sample_data["well_position"] or None
                    if location:
                        if location in well_positions:
                            first_sample = well_positions[location]
                            message = (
                                f"duplicate well position: {location} | {first_sample}"
                                f" - {sample_data['name']}"
                            )
                            raise OrderError(message)
                        well_positions[location] = sample_data["name"]
                    if sample_data["container"] == "96 well plate" and location is None:
                        message = f"missing 'well_position' for sample: {sample_data['name']}"
                        raise ValueError(message)
                    new_sample = {
                        "name": sample_data["name"],
                        "location": location or "1:1",
                        "index_sequence": sample_data["index_sequence"],
                        "udfs": {},
                    }
                    for key, value in sample_data["udfs"].items():
                        if value is None:
                            LOG.debug(f"{key}: skipping null value UDF")
                            continue
                        if key in PROP2UDF:
                            if key in YES_NO_LIMS_BOOLEANS:
                                value = "yes" if value else "no"
                            new_sample["udfs"][PROP2UDF[key]] = value
                        else:
                            LOG.debug(f"UDF not found: {key} - {value}")

                    new_container["samples"].append(new_sample)
                lims_containers.append(new_container)
        return lims_containers

    @staticmethod
    def group_containers(samples):
        """Group samples by containers."""
        tubes = {}
        plates = {}
        no_container = {}
        for sample_data in samples:
            if sample_data["container"] == "Tube":
                # detected tube: name after sample unless specified
                container_name = sample_data.get("container_name") or sample_data["name"]
                if container_name in tubes:
                    raise OrderError(f"{container_name}: conflicting sample/tube name")
                tubes[container_name] = [sample_data]
            elif sample_data["container"] == "96 well plate":
                # detected plate: require container name
                if sample_data["container_name"] not in plates:
                    plates[sample_data["container_name"]] = []
                plates[sample_data["container_name"]].append(sample_data)
            elif sample_data["container"] == "No container":
                # detected no-container: name after sample unless specified
                container_name = sample_data.get("container_name") or sample_data["name"]
                if container_name in tubes:
                    raise OrderError(f"{container_name}: conflicting sample/container name")
                tubes[container_name] = [sample_data]
            else:
                raise ValueError(f"unknown container type: {sample_data['container']}")
        return tubes, plates, no_container
