from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order as OrderResponse
from cg.server.dto.orders.orders_response import OrdersResponse
from cg.services.orders.order_service.utils import (
    create_order_response,
    create_orders_response,
    order_is_closed,
)
from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary
from cg.services.orders.order_summary_service.order_summary_service import (
    OrderSummaryService,
)
from cg.store.models import Order
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

    def set_open(self, order_id: int, open: bool) -> OrderResponse:
        order: Order = self.store.update_order_status(order_id=order_id, open=open)
        return create_order_response(order)

    def update_is_open(self, order_id: int, delivered_analyses: int) -> None:
        """Update the is_open parameter of an order based on the number of delivered analyses."""
        order: Order = self.store.get_order_by_id(order_id)
        case_count: int = len(order.cases)
        if order_is_closed(case_count=case_count, delivered_analyses=delivered_analyses):
            self.set_open(order_id=order_id, open=False)
        elif not order.is_open:
            self.set_open(order_id=order_id, open=True)
