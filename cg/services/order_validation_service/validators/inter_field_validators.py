from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.errors import (
    OrderNameRequiredError,
    TicketNumberRequiredError,
<<<<<<< HEAD
    ValidationError,
)


def validate_ticket_number_required_if_connected(order: Order, **kwargs) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if _ticket_number_is_missing(order):
=======
    OrderValidationError,
)


def validate_ticket_number_required_if_connected(
    order: Order, **kwargs
) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    if _is_ticket_number_missing(order):
>>>>>>> improve-order-flow-main
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


<<<<<<< HEAD
def validate_name_required_for_new_order(order: Order, **kwargs) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if _order_name_is_required(order):
=======
def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    if _is_order_name_required(order):
>>>>>>> improve-order-flow-main
        error = OrderNameRequiredError()
        errors.append(error)
    return errors


<<<<<<< HEAD
def _order_name_is_required(order: Order) -> bool:
    return not order.connect_to_ticket and not order.name


def _ticket_number_is_missing(order: Order) -> bool:
=======
def _is_order_name_required(order: Order) -> bool:
    return False if order.connect_to_ticket else not order.name


def _is_ticket_number_missing(order: Order) -> bool:
>>>>>>> improve-order-flow-main
    return order.connect_to_ticket and not order.ticket_number
