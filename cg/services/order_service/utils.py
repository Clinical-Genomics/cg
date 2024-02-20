from cg.apps.tb.dto.summary_response import Summary
from cg.server.dto.orders.orders_response import Order, OrdersResponse
from cg.store.models import Order as DatabaseOrder


def parse_order(order: DatabaseOrder) -> Order:
    return Order(
        customer_id=order.customer.internal_id,
        ticket_id=order.ticket_id,
        order_date=str(order.order_date.date()),
        order_id=order.id,
        workflow=order.workflow,
    )


def _get_summary_for_order(order: Order, summaries: list[Summary]) -> Summary:
    for summary in summaries:
        if order.order_id == summary.order_id:
            return summary


def create_orders_response(
    database_orders: list[DatabaseOrder], summaries: list[Summary]
) -> OrdersResponse:
    orders: list[Order] = [parse_order(order) for order in database_orders]
    for order in orders:
        summary: Summary = _get_summary_for_order(order, summaries)
        if summary:
            order.summary = summary
    return OrdersResponse(orders=orders)


def create_order_response(order: DatabaseOrder) -> Order:
    return parse_order(order)
