from cg.server.dto.orders.orders_response import Order as PydanticOrder, OrdersResponse
from cg.store.models import Order as DatabaseOrder


def _parse_order(order: DatabaseOrder) -> PydanticOrder:
    return PydanticOrder(
        customer_id=order.customer_id, ticket_id=order.ticket_id, order_date=order.order_date
    )


def create_orders_response(orders: list[DatabaseOrder]) -> OrdersResponse:
    return OrdersResponse(orders=[_parse_order(order) for order in orders])


def create_order_response(order: DatabaseOrder) -> PydanticOrder:
    return _parse_order(order)
