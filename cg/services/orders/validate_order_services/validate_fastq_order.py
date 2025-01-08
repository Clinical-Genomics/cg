from cg.models.orders.order import OrderIn
from cg.services.orders.store_order_services.store_order_service import ValidateOrderService
from cg.store.store import Store


class ValidateFastqOrderService(ValidateOrderService):

    def __init__(self, status_db: Store):
        self.status_db = status_db

    def validate_order(self, order: OrderIn) -> None:
        pass
