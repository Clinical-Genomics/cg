import logging

from cg.apps.lims import LimsAPI
from cg.models.lims.sample import LimsSample
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import OrderInSample

LOG = logging.getLogger(__name__)


class OrderLimsService:

    def __init__(self, lims_api: LimsAPI):
        self.lims_api = lims_api

    @staticmethod
    def _build_lims_sample(customer: str, samples: list[OrderInSample]) -> list[LimsSample]:
        """Convert order input to lims interface input."""
        samples_lims = []
        for sample in samples:
            dict_sample = sample.__dict__
            LOG.debug(f"{sample.name}: prepare LIMS input")
            dict_sample["customer"] = customer
            lims_sample: LimsSample = LimsSample.parse_obj(dict_sample)
            samples_lims.append(lims_sample)
        return samples_lims

    def process_lims(self, lims_order: OrderIn, new_samples: list[OrderInSample]):
        """Process samples to add them to LIMS."""
        samples_lims: list[LimsSample] = self._build_lims_sample(
            lims_order.customer, samples=new_samples
        )
        project_name: str = lims_order.ticket or lims_order.name
        # Create new lims project
        project_data = self.lims_api.submit_project(
            project_name, [lims_sample.dict() for lims_sample in samples_lims]
        )
        lims_map = self.lims_api.get_samples(projectlimsid=project_data["id"], map_ids=True)
        return project_data, lims_map
