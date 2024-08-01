from cg.services.order_validation_service.models.errors import (
    ApplicationNotCompatibleError,
    OrderNameRequiredError,
    TicketNumberRequiredError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.inter_field.rules import (
    validate_application_compatibility,
    validate_name_required_for_new_order,
    validate_ticket_number_required_if_connected,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.store.store import Store


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


def test_application_is_incompatible(
    valid_order: TomteOrder, sample_with_non_compatible_application, base_store: Store
):

    # GIVEN an order that has a sample with an application which is incompatible with the workflow
    valid_order.cases[0].samples.append(sample_with_non_compatible_application)

    # WHEN validating the order
    errors = validate_application_compatibility(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the application compatiblity
    assert isinstance(errors[0], ApplicationNotCompatibleError)
