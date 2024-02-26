from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.server.dto.orders.orders_response import Order, OrderStatusSummary, OrdersResponse
from cg.store.models import Order as DatabaseOrder


def parse_order(order: DatabaseOrder) -> Order:
    return Order(
        customer_id=order.customer.internal_id,
        ticket_id=order.ticket_id,
        order_date=str(order.order_date.date()),
        order_id=order.id,
        workflow=order.workflow,
    )


def create_orders_response(
    orders: list[DatabaseOrder], summaries: list[OrderStatusSummary]
) -> OrdersResponse:
    orders: list[Order] = [parse_order(order) for order in orders]
    _add_summaries(orders=orders, summaries=summaries)
    return OrdersResponse(orders=orders)


def _add_summaries(orders: list[Order], summaries: list[OrderStatusSummary]) -> list[Order]:
    order_map = {order.order_id: order for order in orders}
    for summary in summaries:
        order = order_map[summary.order_id]
        order.summary = summary
    return orders


def create_order_response(order: DatabaseOrder) -> Order:
    return parse_order(order)
