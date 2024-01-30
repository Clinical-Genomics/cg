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


def create_orders_response(database_orders: list[DatabaseOrder]) -> OrdersResponse:
    parsed_database_orders: list[Order] = [parse_order(order) for order in database_orders]
    return OrdersResponse(orders=parsed_database_orders)


def create_order_response(order: DatabaseOrder) -> Order:
    return parse_order(order)
