from cg.services.order_validation_service.models.errors import (
    ApplicationNotCompatibleError,
    InvalidBufferError,
    OrderNameRequiredError,
    SubjectIdSameAsCaseNameError,
    TicketNumberRequiredError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.inter_field.rules import (
    validate_application_compatibility,
    validate_buffers_are_allowed,
    validate_name_required_for_new_order,
    validate_ticket_number_required_if_connected,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.rules import (
    validate_subject_ids_different_from_case_names,
)
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


def test_elution_buffer_is_not_allowed(valid_order: TomteOrder):

    # GIVEN an order with 'skip reception control' toggled but no buffers specfied
    valid_order.skip_reception_control = True

    # WHEN validating that the buffers conform to the 'skip reception control' requirements
    errors = validate_buffers_are_allowed(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the buffer compatability
    assert isinstance(errors[0], InvalidBufferError)


def test_subject_ids_same_as_case_names_not_allowed(valid_order: TomteOrder):

    # GIVEN an order with a sample having its subject_id same as the case's name
    case_name = valid_order.cases[0].name
    valid_order.cases[0].samples[0].subject_id = case_name

    # WHEN validating that no subject ids are the same as the case name
    errors = validate_subject_ids_different_from_case_names(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should be concerning the subject id being the same as the case name
    assert isinstance(errors[0], SubjectIdSameAsCaseNameError)
