from cg.services.order_validation_service.errors.order_errors import (
    OrderNameRequiredError,
    TicketNumberRequiredError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.rules.order.rules import (
    validate_name_required_for_new_order,
    validate_ticket_number_required_if_connected,
)


def test_ticket_is_required(valid_order: Order):
    # GIVEN an order that should be connected to a ticket but is missing a ticket number
    valid_order.connect_to_ticket = True
    valid_order.ticket_number = None

    # WHEN validating the order
    errors = validate_ticket_number_required_if_connected(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the ticket number
    assert isinstance(errors[0], TicketNumberRequiredError)


def test_order_name_is_required(valid_order: Order):

    # GIVEN an order that needs a name but is missing one
    valid_order.name = None
    valid_order.connect_to_ticket = False

    # WHEN validating the order
    errors = validate_name_required_for_new_order(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the name
    assert isinstance(errors[0], OrderNameRequiredError)
