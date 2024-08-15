from cg.models.orders.order import OrderIn
from cg.services.orders.store_order_services.store_generic_order import StoreGenericOrderService
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_rna_fusion_order_service import (
    ValidateRNAFusionOrderService,
)


class RNAFusionOrderSubmitter(OrderSubmitter):

    def __init__(
        self,
        order_validation_service: ValidateRNAFusionOrderService,
        order_store_service: StoreGenericOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order_in: OrderIn) -> dict:
        """Submit a RNA fusion order."""
        self.order_validation_service.validate_order(order_in)
        return self.order_store_service.store_order(order_in)
