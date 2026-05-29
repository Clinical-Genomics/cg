import logging

from genologics.config import BASEURI
from genologics.entities import Artifact
from requests.exceptions import HTTPError

from cg.apps.lims import LimsAPI
from cg.constants import DataDelivery, Workflow
from cg.models.lims.sample import LimsSample
from cg.services.orders.validation.models.sample import Sample

LOG = logging.getLogger(__name__)


class OrderLimsService:

    def __init__(self, lims_api: LimsAPI):
        self.lims_api = lims_api

    @staticmethod
    def _build_lims_sample(
        customer: str,
        samples: list[Sample],
        workflow: Workflow,
        delivery_type: DataDelivery,
        skip_reception_control: bool,
    ) -> list[LimsSample]:
        """Convert order input to LIMS interface input."""
        samples_lims = []
        for sample in samples:
            dict_sample = sample.model_dump()
            LOG.debug(f"{sample.name}: prepare LIMS input")
            dict_sample["customer"] = customer
            dict_sample["data_analysis"] = workflow
            dict_sample["data_delivery"] = delivery_type
            dict_sample["family_name"] = sample._case_name
            if not dict_sample.get("priority"):
                dict_sample["priority"] = sample._case_priority
            if skip_reception_control:
                dict_sample["skip_reception_control"] = True
            if dict_sample.get("source") and dict_sample["source"] == "other":
                dict_sample["source"] = dict_sample.get("source_comment", "other")
            lims_sample: LimsSample = LimsSample.parse_obj(dict_sample)
            samples_lims.append(lims_sample)
        return samples_lims

    def _assign_project_samples_to_workflows(self, project_name: str, samples: list[Sample]):
        """Given a project name and list of store samples of that project, this method will

        for each sample:
        - Find a unique matching LIMS sample by matching project name and customer sample name
        - Collect the appropriate LIMS workflow ID via the Application database table

        for each collected workflow ID:
        - Attempt to route all sample artifacts destined for that workflow via the LIMS API
        """

        # Build dict mapping workflow ID to a list of LIMS artifacts to be routed
        wf_id2arts: dict[str, list[Artifact]] = {}
        for sample in samples:
            # We need to grab the right sample from LIMS w/o knowing the internal ID
            # Use project name and customer name to query for it
            matching_lims_samples: list[LimsSample] = self.lims_api.get_samples(
                projectname=project_name, name=sample.name
            )  # type: ignore
            if len(matching_lims_samples) != 1:
                LOG.error(
                    f"Could not find unique LIMS sample matching project {project_name}"
                    + f" and customer sample name {sample.name}."
                    + " Sample will not be queued."
                )
                continue
            lims_art: Artifact = matching_lims_samples[0].artifact  # type: ignore

            wf_id = 123  # TODO insert new store method here
            if not wf_id:
                LOG.info(
                    f"Sample {lims_art.samples[0].id} has no LIMS workflow ID associated to it's application, skipping."
                )
                continue

            if wf_id not in wf_id2arts:
                wf_id2arts[wf_id] = [lims_art]  # type: ignore
            else:
                wf_id2arts[wf_id].append(lims_art)

        for wf_id, arts in wf_id2arts.items():
            LOG.info(
                f"LIMS project '{project_name}':"
                + f" Routing {len(arts)} artifacts to workflow {wf_id}."
            )
            try:
                self.lims_api.route_artifacts(
                    artifact_list=arts,
                    workflow_uri=f"{BASEURI}/api/v2/configuration/workflows/{wf_id}",
                )
            except HTTPError:
                LOG.exception(f"Failed to add {len(arts)} artifacts to workflow {wf_id}.")
                continue

    def process_lims(
        self,
        samples: list[Sample],
        customer: str,
        ticket: int | None,
        order_name: str,
        workflow: Workflow,
        delivery_type: DataDelivery,
        skip_reception_control: bool,
    ) -> tuple[any, dict]:
        """Process samples to add them to LIMS."""
        samples_lims: list[LimsSample] = self._build_lims_sample(
            customer=customer,
            samples=samples,
            workflow=workflow,
            delivery_type=delivery_type,
            skip_reception_control=skip_reception_control,
        )
        project_name: str = str(ticket) or order_name
        # Create new lims project
        project_data = self.lims_api.submit_project(
            project_name, [lims_sample.dict() for lims_sample in samples_lims]
        )

        self._assign_project_samples_to_workflows(project_name=project_name, samples=samples)

        lims_map: dict[str, str] = self.lims_api.get_samples(
            projectlimsid=project_data["id"], map_ids=True
        )
        return project_data, lims_map
