from cg.server.dto.orders_request import OrdersRequest, OrdersResponse
from cg.store.models import Order
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_orders(self, orders_request: OrdersRequest) -> OrdersResponse:
        orders: list[Order] = self.store.get_orders(orders_request.limit)
        return OrdersResponse(orders=orders)
