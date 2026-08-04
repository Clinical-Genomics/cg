import logging

from genologics.entities import Sample as LimsSample

from cg.apps.lims import LimsAPI
from cg.constants import DataDelivery, Workflow
from cg.models.lims.sample import LimsSample as LimsInputSample
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
    ) -> list[LimsInputSample]:
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
            lims_sample: LimsInputSample = LimsInputSample.parse_obj(dict_sample)
            samples_lims.append(lims_sample)
        return samples_lims

    def process_lims(
        self,
        samples: list[Sample],
        customer: str,
        ticket: int | None,
        order_name: str,
        workflow: Workflow,
        delivery_type: DataDelivery,
        skip_reception_control: bool,
    ) -> tuple[dict[str, str], list[LimsSample]]:
        """Create a project and associated samples in LIMS."""
        samples_lims: list[LimsInputSample] = self._build_lims_sample(
            customer=customer,
            samples=samples,
            workflow=workflow,
            delivery_type=delivery_type,
            skip_reception_control=skip_reception_control,
        )
        project_name: str = str(ticket) or order_name

        project_data, lims_samples = self.lims_api.submit_project(
            project_name, [lims_sample.dict() for lims_sample in samples_lims]
        )

        return project_data, lims_samples
