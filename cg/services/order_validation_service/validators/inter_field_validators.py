from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.errors import (
    TicketNumberRequiredError,
    ValidationError,
)


def validate_ticket_number_required_if_connected(order: Order, **kwargs) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if _ticket_number_is_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def _ticket_number_is_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number
