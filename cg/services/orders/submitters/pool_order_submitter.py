from cg.services.order_validation_service.models.sample_aliases import OrderWithIndexedSamples
from cg.services.orders.store_order_services.store_pool_order import StorePoolOrderService
from cg.services.orders.submitters.order_submitter import OrderSubmitter
from cg.services.orders.validate_order_services.validate_pool_order import ValidatePoolOrderService


class PoolOrderSubmitter(OrderSubmitter):
    """
    Class for submitting pool orders.
    This class is used to submit orders for the following workflows:
    - Fluffy
    - RML (Ready made libraries)

    """

    def __init__(
        self,
        order_validation_service: ValidatePoolOrderService,
        order_store_service: StorePoolOrderService,
    ):
        self.order_validation_service = order_validation_service
        self.order_store_service = order_store_service

    def submit_order(self, order: OrderWithIndexedSamples) -> dict:
        return self.order_store_service.store_order(order)
