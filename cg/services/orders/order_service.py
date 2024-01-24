from cg.server.dto.orders_request import OrdersRequest
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_orders(self, orders_request: OrdersRequest):
        return self.store.get_orders(orders_request.limit)
