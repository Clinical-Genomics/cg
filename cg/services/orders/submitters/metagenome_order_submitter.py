from cg.services.orders.store_order_services.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_metagenome_order import (
    ValidateMetagenomeOrderService,
)


class MetagenomeOrderSubmitter(OrderSubmitter):
    """Class for submitting metagenome and taxprofiler orders."""

    def __init__(
        self,
        order_validation_service: ValidateMetagenomeOrderService,
        order_store_service: StoreMetagenomeOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order_in) -> dict:
        """Submit a metagenome order."""
        self.order_validation_service.validate_order(order_in)
        return self.order_store_service.store_order(order_in)
