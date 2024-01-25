from cg.server.dto.orders.orders_response import Order as PydanticOrder
from cg.store.models import Order as DatabaseOrder


def parse_order(order: DatabaseOrder) -> PydanticOrder:
    return PydanticOrder(
        customer_id=order.customer_id, ticket_id=order.ticket_id, order_date=order.order_date
    )
