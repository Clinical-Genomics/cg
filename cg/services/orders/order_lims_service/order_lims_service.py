import logging

from cg.apps.lims import LimsAPI
from cg.models.lims.sample import LimsSample
from cg.services.order_validation_service.models.sample import Sample

LOG = logging.getLogger(__name__)


class OrderLimsService:

    def __init__(self, lims_api: LimsAPI):
        self.lims_api = lims_api

    @staticmethod
    def _build_lims_sample(customer: str, samples: list[Sample]) -> list[LimsSample]:
        """Convert order input to lims interface input."""
        samples_lims = []
        for sample in samples:
            dict_sample = sample.model_dump()
            LOG.debug(f"{sample.name}: prepare LIMS input")
            dict_sample["customer"] = customer
            lims_sample: LimsSample = LimsSample.parse_obj(dict_sample)
            samples_lims.append(lims_sample)
        return samples_lims

    def process_lims(self, samples: list[Sample], customer: str, ticket: int, order_name: str):
        """Process samples to add them to LIMS."""
        samples_lims: list[LimsSample] = self._build_lims_sample(customer=customer, samples=samples)
        project_name: str = str(ticket) or order_name
        # Create new lims project
        project_data = self.lims_api.submit_project(
            project_name, [lims_sample.dict() for lims_sample in samples_lims]
        )
        lims_map = self.lims_api.get_samples(projectlimsid=project_data["id"], map_ids=True)
        return project_data, lims_map
