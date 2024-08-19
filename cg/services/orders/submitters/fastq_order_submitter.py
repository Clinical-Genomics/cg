from cg.models.orders.order import OrderIn
from cg.services.orders.store_order_services.store_fastq_order_service import StoreFastqOrderService
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_fastq_order import (
    ValidateFastqOrderService,
)


class FastqOrderSubmitter(OrderSubmitter):
    """Submitter for fastq orders."""

    def __init__(
        self,
        order_validation_service: ValidateFastqOrderService,
        order_store_service: StoreFastqOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order_in: OrderIn) -> dict:
        """Submit a fastq order."""
        self.order_validation_service.validate_order(order_in)
        result: dict = self.order_store_service.store_order(order_in)
        return result
