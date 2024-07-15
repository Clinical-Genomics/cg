from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.validation_error import (
    ValidationError,
    ValidationErrors,
)
from cg.services.order_validation_service.validators.utils import _create_order_error


def validate_ticket_number_required_if_connected(order: Order, **kwargs) -> ValidationErrors | None:
    if _ticket_number_is_missing(order):
        return _create_missing_ticket_error()


def _create_missing_ticket_error() -> ValidationErrors:
    field = "ticket_number"
    message = "Ticket number is required when connecting to ticket"
    return _create_order_error(message=message, field=field)


def _ticket_number_is_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number
