from typing import List

from cg.exc import OrderError
from cg.meta.orders.microbial_submitter import MicrobialSubmitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import SarsCov2Sample
from cg.store.models import Customer


class SarsCov2Submitter(MicrobialSubmitter):
    """Class for validating Sars-Cov submissions."""

    def validate_order(self, order: OrderIn) -> None:
        """Validate order sample names."""
        super().validate_order(order=order)
        self._validate_sample_names_are_available(samples=order.samples, customer_id=order.customer)

    def _validate_sample_names_are_available(
        self, samples: List[SarsCov2Sample], customer_id: str
    ) -> None:
        """Validate names of all samples are not already in use."""
        customer: Customer = self.status.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        for sample in samples:
            if sample.control:
                continue
            if self.status.get_sample_by_customer_and_name(
                customer_entry_id=[customer.id], sample_name=sample.name
            ):
                raise OrderError(
                    f"Sample name {sample.name} already in use for customer {customer.name}"
                )
