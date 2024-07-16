from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.errors import (
    OrderNameRequiredError,
    TicketNumberRequiredError,
    OrderValidationError,
)


def validate_ticket_number_required_if_connected(order: Order, **kwargs) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    if _ticket_number_is_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    if _order_name_is_required(order):
        error = OrderNameRequiredError()
        errors.append(error)
    return errors


def _order_name_is_required(order: Order) -> bool:
    return not order.connect_to_ticket and not order.name


def _ticket_number_is_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number
