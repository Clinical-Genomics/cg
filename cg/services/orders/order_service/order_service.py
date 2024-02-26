from cg.models.orders.order import OrderIn
from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order as OrderResponse
from cg.server.dto.orders.orders_response import OrdersResponse
from cg.services.orders.order_service.exceptions import OrderNotFoundError
from cg.services.orders.order_service.utils import (
    create_order_response,
    create_orders_response,
)
from cg.services.orders.order_status_service import OrderStatusService
from cg.services.orders.order_status_service.dto.order_status_summary import OrderSummary
from cg.store.models import Order
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store, summary_service: OrderStatusService) -> None:
        self.store = store
        self.summary_service = summary_service

    def get_order(self, order_id: int) -> OrderResponse:
        order: Order | None = self.store.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        return create_order_response(order)

    def get_orders(self, orders_request: OrdersRequest) -> OrdersResponse:
        orders: list[Order] = self.store.get_orders(orders_request)

        summaries: list[OrderSummary] = []
        if orders_request.include_summary:
            order_ids: list[int] = [order.id for order in orders]
            summaries = self.summary_service.get_status_summaries(order_ids)

        return create_orders_response(orders=orders, summaries=summaries)

    def create_order(self, order_data: OrderIn) -> OrderResponse:
        """Creates an order and links it to the given cases."""
        order: Order = self.store.add_order(order_data)
        cases = self.store.get_cases_by_ticket_id(order_data.ticket)
        for case in cases:
            self.store.link_case_to_order(order_id=order.id, case_id=case.id)
        return create_order_response(order)
