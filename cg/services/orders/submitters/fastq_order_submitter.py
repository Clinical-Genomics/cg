from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.fastq.validation_service import (
    FastqValidationService,
)
from cg.services.orders.store_order_services.store_fastq_order_service import StoreFastqOrderService
from cg.services.orders.submitters.order_submitter import OrderSubmitter


class FastqOrderSubmitter(OrderSubmitter):
    """Submitter for fastq orders."""

    def __init__(
        self,
        order_validation_service: FastqValidationService,
        order_store_service: StoreFastqOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order: FastqOrder) -> dict:
        """Submit a fastq order."""
        result: dict = self.order_store_service.store_order(order)
        return result
