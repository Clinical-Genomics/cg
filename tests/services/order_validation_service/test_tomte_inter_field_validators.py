from cg.services.order_validation_service.models.errors import (
    OccupiedWellError,
    RepeatedSampleNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.rules import (
    validate_unique_sample_names_in_cases,
    validate_wells_contain_at_most_one_sample,
)


def test_multiple_samples_in_well_not_allowed(order_with_samples_in_same_well: TomteOrder):

    # GIVEN an order with multiple samples in the same well

    # WHEN validating the order
    errors = validate_wells_contain_at_most_one_sample(order_with_samples_in_same_well)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the well
    assert isinstance(errors[0], OccupiedWellError)


def test_order_without_multiple_samples_in_well(valid_order: TomteOrder):

    # GIVEN a valid order with no samples in the same well

    # WHEN validating the order
    errors = validate_wells_contain_at_most_one_sample(valid_order)

    # THEN no errors should be returned
    assert not errors


def test_duplicate_sample_names_not_allowed(order_with_duplicate_sample_names: TomteOrder):
    # Given an order with samples in a case with the same name

    # WHEN validating the order
    errors = validate_unique_sample_names_in_cases(order_with_duplicate_sample_names)

    # THEN errors are returned
    assert errors

    # THEN the errors are about the sample names
    assert isinstance(errors[0], RepeatedSampleNameError)
