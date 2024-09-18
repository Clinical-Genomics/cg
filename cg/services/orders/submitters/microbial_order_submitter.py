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
    - Sars-Cov-2
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

    def submit_order(self, order_in) -> dict:
        """Submit a microbial order."""
        self.order_validation_service.validate_order(order_in)
        return self.order_store_service.store_order(order_in)
