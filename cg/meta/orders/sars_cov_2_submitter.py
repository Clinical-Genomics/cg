from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.exc import OrderError
from cg.meta.orders.microbial_submitter import MicrobialSubmitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import OrderInSample, SarsCov2Sample
from cg.store import models
import datetime as dt


class SarsCov2Submitter(MicrobialSubmitter):
    def validate_order(self, order: OrderIn) -> None:
        super().validate_order(order=order)
        self._validate_sample_names_are_available(samples=order.samples, customer_id=order.customer)

    def _validate_sample_names_are_available(
        self, samples: List[SarsCov2Sample], customer_id: str
    ) -> None:
        """Validate that the names of all samples are unused for all samples"""
        customer_obj: models.Customer = self.status.customer(customer_id)

        sample: SarsCov2Sample
        for sample in samples:
            sample_name: str = sample.name

            if sample.control:
                continue

            if self.status.find_samples(customer=customer_obj, name=sample_name).first():
                raise OrderError(
                    f"Sample name {sample_name} already in use for customer {customer_obj.name}"
                )
