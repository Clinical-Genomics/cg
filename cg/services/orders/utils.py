from cg.server.dto.orders.orders_response import Order
from cg.store.models import Order as DatabaseOrder


def parse_order(order: DatabaseOrder) -> Order:
    return Order(
        customer_id=order.customer.internal_id,
        ticket_id=order.ticket_id,
        order_date=order.order_date.date(),
        order_id=order.id,
        workflow=order.workflow,
    )
