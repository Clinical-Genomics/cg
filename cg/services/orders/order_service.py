from cg.exc import OrderNotFoundError
from cg.models.orders.order import OrderIn
from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order as OrderResponse
from cg.server.dto.orders.orders_response import OrdersResponse
from cg.services.orders.utils import create_order_response, create_orders_response
from cg.store.models import Order
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_order(self, order_id: int) -> OrderResponse:
        order: Order | None = self.store.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        return create_order_response(order)

    def get_orders(self, orders_request: OrdersRequest) -> OrdersResponse:
        orders: list[Order] = self.store.get_orders(orders_request)
        return create_orders_response(orders)

    def create_order(self, order_data: OrderIn) -> OrderResponse:
        order: Order = self.store.add_order(order_data)
        return create_order_response(order)
