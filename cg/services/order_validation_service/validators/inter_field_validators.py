from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.validation_error import (
    ValidationError,
    ValidationErrors,
)


def validate_ticket_number_required_if_connected(order: Order) -> ValidationErrors | None:
    if _ticket_number_is_missing(order):
        return _create_missing_ticket_error(order)


def _create_missing_ticket_error() -> ValidationErrors:
    field = "ticket_number"
    message = "Ticket number is required when connecting to ticket"
    return _create_order_error(message=message, field=field)


def _ticket_number_is_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number


def _create_order_error(message: str, field: str) -> ValidationErrors:
    error: ValidationError = _create_error(field=field, message=message)
    return _create_errors(error)


def _create_errors(error: ValidationError) -> ValidationErrors:
    return ValidationErrors(errors=[error])


def _create_error(field: str, message: str) -> ValidationError:
    return ValidationError(field=field, message=message)
