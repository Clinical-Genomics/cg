from cg.services.order_validation_service.workflows.pacbio_long_read.models.order import PacbioOrder
from cg.services.orders.store_order_services.store_pacbio_order_service import (
    StorePacBioOrderService,
)
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_pacbio_order import (
    ValidatePacbioOrderService,
)


class PacbioOrderSubmitter(OrderSubmitter):
    """Submitter for Pacbio orders."""

    def __init__(
        self,
        order_validation_service: ValidatePacbioOrderService,
        order_store_service: StorePacBioOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order: PacbioOrder) -> dict:
        """Submit a fastq order."""
        result: dict = self.order_store_service.store_order(order=order)
        return result
