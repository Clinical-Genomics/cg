# -*- coding: utf-8 -*-
from typing import List
import logging
from xml.etree import ElementTree

from genologics.entities import Project, Researcher, Sample, Container, Containertype, Artifact

from cg.exc import OrderError

LOG = logging.getLogger(__name__)
CONTAINER_TYPE_MAP = {'Tube': 2, '96 well plate': 1}
PROP2UDF = {
    'require_qcok': 'Process only if QC OK',
    'application': 'Sequencing Analysis',
    'priority': 'priority',
    'source': 'Source',
    'comment': 'Comment',
    'customer': 'customer',
    'family_name': 'familyID',
    'quantity': 'Quantity',
    'tumour': 'tumor',
    'pool': 'pool name',
    'index': 'Index type',
    'index_number': 'Index number',
    'concentration': 'Concentration (nM)',
    'volume': 'Volume (uL)',
    'well_position_rml': 'RML well position',
    'rml_plate_name': 'RML plate name',
}


class OrderHandler:

    def add_project(self, project_name: str, samples: List[dict], researcher_id: str='3'):
        """Submit a new order.

        Example:

            [{
                'name': '17081-II-1U',
                'container': '96 well plate',
                'container_name': 'CMMS',
                'well_position': 'A:1',
                'udfs': {
                    'priority': 'standard',
                    'application': 'WGTPCFC030',
                    'require_qcok': True,
                    'quantity': "2200",
                    'source': 'blood',
                    'customer': 'cust003',
                },
            }]

        Args:
            data (dict): project order data dict
            researcher_id (Optional[str]): id of research to link to the order

        Returns:
            genologics.entities.Project: new LIMS project instance
        """
        containers = self.prepare(samples)
        lims_project = self.submit(project_name, researcher_id, containers)
        lims_project_data = self._export_project(lims_project)
        return lims_project_data

    def submit(self, project_name: str, researcher_id: str, containers: List[dict]):
        """Submit a new project with samples to LIMS."""
        LOG.debug('creating LIMS project')
        lims_researcher = Researcher(self, id=researcher_id)
        lims_project = Project.create(self, researcher=lims_researcher, name=project_name)
        LOG.info("created new LIMS project: %s", lims_project.id)

        for container_data in containers:
            LOG.debug('creating LIMS container')
            container_type = Containertype(lims=self, id=container_data['type'])
            lims_container = Container.create(lims=self, name=container_data['name'],
                                              type=container_type)
            LOG.info("created new LIMS container: %s", lims_container.id)

            for sample_data in container_data['samples']:
                LOG.debug("creating LIMS sample: %s", sample_data['name'])
                raw_sample = Sample._create(self, creation_tag='samplecreation',
                                            name=sample_data['name'], project=lims_project)

                LOG.debug('adding sample UDFs')
                for udf_key, udf_value in sample_data['udfs'].items():
                    if udf_value:
                        raw_sample.udf[udf_key] = udf_value

                location_label = sample_data['location']
                lims_sample = self._save_sample(raw_sample, lims_container, location_label)
                LOG.info("created new LIMS sample: %s -> %s", lims_sample.name, lims_sample.id)

                if sample_data['index_sequence']:
                    LOG.info("adding index seq./reagent label %s", sample_data['index_sequence'])
                    self._save_reagentlabel(
                        artifact=lims_sample.artifact,
                        reagent_label=sample_data['index_sequence'],
                        sample_name=lims_sample.name,
                    )
        return lims_project

    @classmethod
    def prepare(cls, samples):
        """Convert API input to LIMS input data."""
        lims_containers = []
        tubes, plates = cls.group_containers(samples)
        # "96 well plate" = container type "1"; Tube = container type "2"
        for container_type, containers in [('1', plates), ('2', tubes)]:
            for container_name, samples in containers.items():
                new_container = {
                    'name': container_name,
                    'type': container_type,
                    'samples': [],
                }
                # check that positions in plate are unique
                well_positions = {}
                for sample_data in samples:
                    location = sample_data['well_position'] or None
                    if location:
                        if location in well_positions:
                            first_sample = well_positions[location]
                            message = (f"duplicate well position: {location} | {first_sample}"
                                       f" - {sample_data['name']}")
                            raise OrderError(message)
                        well_positions[location] = sample_data['name']
                    if sample_data['container'] == '96 well plate' and location is None:
                        message = f"missing 'well_position' for sample: {sample_data['name']}"
                        raise ValueError(message)
                    new_sample = {
                        'name': sample_data['name'],
                        'location': location or '1:1',
                        'index_sequence': sample_data['index_sequence'],
                        'udfs': {}
                    }
                    for key, value in sample_data['udfs'].items():
                        if key in PROP2UDF:
                            if isinstance(value, bool):
                                value = 'yes' if value else 'no'
                            new_sample['udfs'][PROP2UDF[key]] = value
                        else:
                            LOG.debug(f"UDF not found: {key} - {value}")

                    new_container['samples'].append(new_sample)
                lims_containers.append(new_container)
        return lims_containers

    @staticmethod
    def group_containers(samples):
        """Group samples by containers."""
        tubes = {}
        plates = {}
        for sample_data in samples:
            if sample_data['container'] == 'Tube':
                # detected tube: name after sample unless specified
                container_name = sample_data.get('container_name') or sample_data['name']
                tubes[container_name] = [sample_data]
            elif sample_data['container'] == '96 well plate':
                # detected plate: require container name
                if sample_data['container_name'] not in plates:
                    plates[sample_data['container_name']] = []
                plates[sample_data['container_name']].append(sample_data)
            else:
                raise ValueError(f"unknown container type: {sample_data['container']}")
        return tubes, plates

    def _save_sample(self, instance, container, location_label):
        """Create an instance of Sample from attributes then post it to the LIMS"""
        location = ElementTree.SubElement(instance.root, 'location')
        ElementTree.SubElement(location, 'container', dict(uri=container.uri))
        location_element = ElementTree.SubElement(location, 'value')
        location_element.text = location_label
        data = self.tostring(ElementTree.ElementTree(instance.root))
        instance.root = self.post(uri=self.get_uri(Sample._URI), data=data)
        instance._uri = instance.root.attrib['uri']
        return instance

    def _save_reagentlabel(self, artifact: Artifact, reagent_label: str, sample_name: str=None):
        """Update artifact with reagent label."""
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
        <art:artifact xmlns:art="http://genologics.com/ri/artifact">
        <name>{sample_name or artifact.id}</name>
        <reagent-label name="{reagent_label}"></reagent-label>
        </art:artifact>"""
        self.put(artifact.uri.split('?')[0], xml_data)
