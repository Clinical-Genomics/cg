from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order, OrdersResponse
from cg.services.orders.utils import parse_order
from cg.store.models import Order as DatabaseOrder
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_orders(self, orders_request: OrdersRequest) -> OrdersResponse:
        database_orders: list[DatabaseOrder] = self.store.get_orders(orders_request.limit)
        parsed_orders: list[Order] = [parse_order(order) for order in database_orders]
        return OrdersResponse(orders=parsed_orders)
