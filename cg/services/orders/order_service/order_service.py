from cg.server.dto.orders.orders_request import OrdersRequest
from cg.server.dto.orders.orders_response import Order, OrdersResponse
from cg.services.orders.order_service.models import OrderQueryParams
from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary
from cg.services.orders.order_summary_service.order_summary_service import OrderSummaryService
from cg.store.models import Order as DbOrder
from cg.store.store import Store


class OrderService:
    def __init__(self, store: Store, status_service: OrderSummaryService) -> None:
        self.store = store
        self.summary_service = status_service

    def get_order(self, order_id: int) -> Order:
        order: DbOrder = self.store.get_order_by_id(order_id)
        summary: OrderSummary = self.summary_service.get_summary(order_id)
        return self._create_order_response(order=order, summary=summary)

    def get_orders(self, orders_request: OrdersRequest) -> OrdersResponse:
        order_query_params: OrderQueryParams = self._get_order_query_params(orders_request)
        orders, total_count = self.store.get_orders(order_query_params)
        order_ids: list[int] = [order.id for order in orders]
        if not order_ids:
            return OrdersResponse(orders=[], total_count=0)
        summaries: list[OrderSummary] = self.summary_service.get_summaries(order_ids)
        return self._create_orders_response(orders=orders, summaries=summaries, total=total_count)

    def set_open(self, order_id: int, open: bool) -> Order:
        order: DbOrder = self.store.update_order_status(order_id=order_id, open=open)
        return self._create_order_response(order)

    def update_is_open(self, order_id: int, delivered_analyses: int) -> None:
        """Update the is_open parameter of an order based on the number of delivered analyses."""
        order: DbOrder = self.store.get_order_by_id(order_id)
        case_count: int = len(order.cases)
        if self._is_order_closed(case_count=case_count, delivered_analyses=delivered_analyses):
            self.set_open(order_id=order_id, open=False)
        elif not order.is_open:
            self.set_open(order_id=order_id, open=True)

    @staticmethod
    def _get_order_query_params(orders_request: OrdersRequest) -> OrderQueryParams:
        return OrderQueryParams(
            page=orders_request.page,
            page_size=orders_request.page_size,
            search=orders_request.search,
            is_open=orders_request.is_open,
            sort_field=orders_request.sort_field,
            sort_order=orders_request.sort_order,
            workflows=[orders_request.workflow] if orders_request.workflow else [],
        )

    @staticmethod
    def _create_order_response(order: DbOrder, summary: OrderSummary | None = None) -> Order:
        return Order(
            customer_id=order.customer.internal_id,
            ticket_id=order.ticket_id,
            order_date=str(order.order_date.date()),
            id=order.id,
            is_open=order.is_open,
            workflow=order.workflow,
            summary=summary,
        )

    def _create_orders_response(
        self, orders: list[DbOrder], summaries: list[OrderSummary], total: int
    ) -> OrdersResponse:
        orders: list[Order] = [self._create_order_response(order) for order in orders]
        self._add_summaries(orders=orders, summaries=summaries)
        return OrdersResponse(orders=orders, total_count=total)

    @staticmethod
    def _add_summaries(orders: list[Order], summaries: list[OrderSummary]) -> list[Order]:
        order_map = {order.id: order for order in orders}
        for summary in summaries:
            order = order_map[summary.order_id]
            order.summary = summary
        return orders

    @staticmethod
    def _is_order_closed(case_count: int, delivered_analyses: int) -> bool:
        return delivered_analyses >= case_count
