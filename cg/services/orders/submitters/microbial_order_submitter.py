from cg.services.order_validation_service.workflows.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.orders.store_order_services.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.services.orders.store_order_services.store_microbial_order import StoreMicrobialOrderService
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_microbial_order import (
    ValidateMicrobialOrderService,
)


class MicrobialOrderSubmitter(OrderSubmitter):
    """
    Class for submitting microbial orders.
    This class is used to submit orders for the following workflows:
    - Microsalt
    - Microbial fastq
    - Mutant
    """

    def __init__(
        self,
        order_validation_service: ValidateMicrobialOrderService,
        order_store_service: StoreMicrobialOrderService | StoreMicrobialFastqOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order: MutantOrder | MicrosaltOrder | MicrobialFastqOrder) -> dict:
        """Submit a microbial order."""
        return self.order_store_service.store_order(order)
