from cg.models.orders.order import OrderIn
from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order as OrderResponse
from cg.server.dto.orders.orders_response import OrdersResponse
from cg.services.orders.order_service.utils import (
    create_order_response,
    create_orders_response,
    order_is_delivered,
)
from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary
from cg.services.orders.order_summary_service.order_summary_service import (
    OrderSummaryService,
)
from cg.store.models import Case, Order
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store, status_service: OrderSummaryService) -> None:
        self.store = store
        self.summary_service = status_service

    def get_order(self, order_id: int) -> OrderResponse:
        order: Order = self.store.get_order_by_id(order_id)
        summary: OrderSummary = self.summary_service.get_summary(order_id)
        return create_order_response(order=order, summary=summary)

    def get_orders(self, orders_request: OrdersRequest) -> OrdersResponse:
        orders, total_count = self.store.get_orders(orders_request)
        order_ids: list[int] = [order.id for order in orders]
        if not order_ids:
            return OrdersResponse(orders=[], total_count=0)
        summaries: list[OrderSummary] = self.summary_service.get_summaries(order_ids)
        return create_orders_response(orders=orders, summaries=summaries, total=total_count)

    def create_order(self, order_data: OrderIn) -> OrderResponse:
        """Creates an order and links it to the given cases."""
        order: Order = self.store.add_order(order_data)
        cases: list[Case] = self.store.get_cases_by_ticket_id(order_data.ticket)
        for case in cases:
            self.store.link_case_to_order(order_id=order.id, case_id=case.id)
        return create_order_response(order)

    def set_delivery(self, order_id: int, delivered: bool) -> OrderResponse:
        order: Order = self.store.update_order_delivery(order_id=order_id, delivered=delivered)
        return create_order_response(order)

    def update_delivered(self, order_id: int, delivered_analyses: int) -> None:
        """Update the delivery status of an order based on the number of delivered analyses."""
        order: Order = self.store.get_order_by_id(order_id)
        case_count: int = len(order.cases)
        if order_is_delivered(case_count=case_count, delivered_analyses=delivered_analyses):
            self.set_delivery(order_id=order_id, delivered=True)
        elif order.is_delivered:
            self.set_delivery(order_id=order_id, delivered=False)
