from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.errors import (
    OrderNameRequiredError,
    TicketNumberRequiredError,
    OrderError,
)
from cg.services.order_validation_service.validators.inter_field.utils import (
    _is_order_name_required,
    _is_ticket_number_missing,
)


def validate_ticket_number_required_if_connected(order: Order, **kwargs) -> list[OrderError]:
    errors: list[OrderError] = []
    if _is_ticket_number_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderError]:
    errors: list[OrderError] = []
    if _is_order_name_required(order):
        error = OrderNameRequiredError()
        errors.append(error)
    return errors
