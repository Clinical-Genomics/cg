from cg.apps.tb.dto.summary_response import Summary
from cg.server.dto.orders.orders_response import Order, OrderSummary, OrdersResponse
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
    database_orders: list[DatabaseOrder], summaries: list[Summary]
) -> OrdersResponse:
    orders = [parse_order(order) for order in database_orders]
    if summaries:
        _add_summaries_to_orders(orders=orders, summaries=summaries)
    return OrdersResponse(orders=orders)


def _add_summaries_to_orders(orders: list[Order], summaries: list[Summary]) -> list[Order]:
    summary_mapping: dict = {summary.order_id: summary for summary in summaries}
    for order in orders:
        summary: Summary = summary_mapping.get(order.order_id)
        if summary:
            order.summary = OrderSummary(
                total=get_total_cases_in_order(order),
                delivered=summary.delivered,
                running=summary.running,
                cancelled=summary.cancelled,
                failed=summary.failed,
            )
    return orders


def get_total_cases_in_order(order: DatabaseOrder) -> int:
    return len(order.cases)


def create_order_response(order: DatabaseOrder) -> Order:
    return parse_order(order)
