from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.errors import (
    OrderNameRequiredError,
    TicketNumberRequiredError,
    OrderValidationError,
)


def validate_ticket_number_required_if_connected(
    order: Order, **kwargs
) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    if _is_ticket_number_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    if _is_order_name_required(order):
        error = OrderNameRequiredError()
        errors.append(error)
    return errors


def _is_order_name_required(order: Order) -> bool:
    return False if order.connect_to_ticket else not order.name


def _is_ticket_number_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number
