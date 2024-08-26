import pytest

from cg.services.order_validation_service.errors.case_sample_errors import (
    ApplicationNotCompatibleError,
    ContainerNameMissingError,
    InvalidVolumeError,
    SubjectIdSameAsCaseNameError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.errors.order_errors import (
    OrderNameRequiredError,
    TicketNumberRequiredError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.rules.case_sample.rules import (
    validate_application_compatibility,
    validate_container_name_required,
    validate_volume_interval,
    validate_well_positions_required,
)
from cg.services.order_validation_service.rules.order.rules import (
    validate_name_required_for_new_order,
    validate_ticket_number_required_if_connected,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)
from cg.services.order_validation_service.rules.case_sample.rules import (
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
    valid_order: TomteOrder, sample_with_non_compatible_application: TomteSample, base_store: Store
):

    # GIVEN an order that has a sample with an application which is incompatible with the workflow
    valid_order.cases[0].samples.append(sample_with_non_compatible_application)

    # WHEN validating the order
    errors = validate_application_compatibility(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the application compatability
    assert isinstance(errors[0], ApplicationNotCompatibleError)


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


def test_well_position_missing(
    valid_order: TomteOrder, sample_with_missing_well_position: TomteSample
):

    # GIVEN an order with a sample with a missing well position
    valid_order.cases[0].samples.append(sample_with_missing_well_position)

    # WHEN validating that no well positions are missing
    errors = validate_well_positions_required(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing well position
    assert isinstance(errors[0], WellPositionMissingError)


def test_container_name_missing(
    valid_order: TomteOrder, sample_with_missing_container_name: TomteSample
):

    # GIVEN an order with a sample missing its container name
    valid_order.cases[0].samples.append(sample_with_missing_container_name)

    # WHEN validating that it is not missing any container names
    errors = validate_container_name_required(order=valid_order)

    # THEN an error should be raised
    assert errors

    # THEN the error should concern the missing container name
    assert isinstance(errors[0], ContainerNameMissingError)


@pytest.mark.parametrize("sample_volume", [1, 200])
def test_volume_out_of_bounds(valid_order: TomteOrder, sample_volume: int):

    # GIVEN an order containing a sample with an invalid volume
    valid_order.cases[0].samples[0].volume = sample_volume

    # WHEN validating that the volume is within bounds
    errors = validate_volume_interval(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid volume
    assert isinstance(errors[0], InvalidVolumeError)


def test_volume_in_bounds(valid_order: TomteOrder):

    # GIVEN a valid order

    # WHEN validating that the volume is within bounds
    errors = validate_volume_interval(valid_order)

    # THEN no error should be returned
    assert not errors
