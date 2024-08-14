from datetime import datetime

from cg.meta.orders.lims import process_lims
from cg.meta.orders.microbial_fastq_submitter.models import MicrobialFastqDTO
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn
from cg.store.models import Sample


class MicrobialFastqSubmitter(Submitter):
    def validate_order(self, order: OrderIn) -> None:
        """Part of Submitter interface, base implementation"""

    def submit_order(self, order: OrderIn) -> dict:
        project_data, lims_map = process_lims(
            lims_api=self.lims, lims_order=order, new_samples=order.samples
        )

    @staticmethod
    def order_to_status(order: OrderIn) -> MicrobialFastqDTO:
        """Convert order input for microbial samples."""
        order_samples: list[dict] = order.samples
        db_samples: list[Sample] = [Sample() for sample in order_samples]
        return MicrobialFastqDTO(customer=order.customer, order=order.name, samples=db_samples)

    def store_items_in_status(
        self, customer_id: str, order: str, ordered: datetime, ticket_id: int, items: list[dict]
    ) -> list[Sample]:
        pass
