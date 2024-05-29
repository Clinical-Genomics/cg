from cg.server.dto.orders.orders_response import Order, OrdersResponse, OrderSummary
from cg.store.models import Order as DatabaseOrder


def create_order_response(order: DatabaseOrder, summary: OrderSummary | None = None) -> Order:
    return Order(
        customer_id=order.customer.internal_id,
        ticket_id=order.ticket_id,
        order_date=str(order.order_date.date()),
        id=order.id,
        is_delivered=order.is_delivered,
        workflow=order.workflow,
        summary=summary,
    )


def create_orders_response(
    orders: list[DatabaseOrder], summaries: list[OrderSummary], total: int
) -> OrdersResponse:
    orders: list[Order] = [create_order_response(order) for order in orders]
    _add_summaries(orders=orders, summaries=summaries)
    return OrdersResponse(orders=orders, total_count=total)


def _add_summaries(orders: list[Order], summaries: list[OrderSummary]) -> list[Order]:
    order_map = {order.id: order for order in orders}
    for summary in summaries:
        order = order_map[summary.order_id]
        order.summary = summary
    return orders


def order_is_delivered(case_count: int, delivered_analyses: int) -> bool:
    return delivered_analyses >= case_count
