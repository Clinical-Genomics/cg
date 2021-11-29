from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.lims import process_lims
from cg.meta.orders.microbial_submitter import MicrobialSubmitter
from cg.meta.orders.submitter import Submitter
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import StatusEnum
from cg.models.orders.samples import OrderInSample
from cg.store import models
import datetime as dt


class SarsCov2Submitter(MicrobialSubmitter):
    def validate_order(self, order: OrderIn) -> None:
        self._validate_sample_names_are_available(
            project=OrderType.SARS_COV_2, samples=order.samples, customer_id=order.customer
        )

    def _validate_sample_names_are_available(
        self, project: OrderType, samples: List[dict], customer_id: str
    ) -> None:
        """Validate that the names of all samples are unused for all samples"""

        # TODO: Remove this check
        if project is not OrderType.SARS_COV_2:
            return

        customer_obj: models.Customer = self.status.customer(customer_id)

        for sample in samples:

            sample_name: str = sample.name

            if self._existing_sample(sample):
                continue

            if self.status.find_samples(customer=customer_obj, name=sample_name).first():
                raise OrderError(
                    f"Sample name {sample_name} already in use for customer {customer_id}"
                )

    @staticmethod
    def _existing_sample(sample: OrderInSample) -> bool:
        return hasattr(sample, "internal_id") and sample.internal_id is not None
