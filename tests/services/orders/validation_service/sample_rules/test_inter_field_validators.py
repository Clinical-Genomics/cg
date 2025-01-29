from cg.services.orders.validation.errors.sample_errors import (
    OccupiedWellError,
    SampleNameRepeatedError,
)
from cg.services.orders.validation.rules.sample.rules import (
    validate_sample_names_unique,
    validate_wells_contain_at_most_one_sample,
)
from cg.services.orders.validation.workflows.microsalt.models.order import MicrosaltOrder


def test_multiple_samples_in_well_not_allowed(order_with_samples_in_same_well: MicrosaltOrder):

    # GIVEN an order with multiple samples in the same well

    # WHEN validating the order
    errors = validate_wells_contain_at_most_one_sample(order_with_samples_in_same_well)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the well
    assert isinstance(errors[0], OccupiedWellError)


def test_order_without_multiple_samples_in_well(valid_microsalt_order: MicrosaltOrder):

    # GIVEN a valid order with no samples in the same well

    # WHEN validating the order
    errors = validate_wells_contain_at_most_one_sample(valid_microsalt_order)

    # THEN no errors should be returned
    assert not errors


def test_sample_name_repeated(valid_microsalt_order: MicrosaltOrder):

    # GIVEN a valid order within sample names are repeated
    sample_name_1 = valid_microsalt_order.samples[0].name
    valid_microsalt_order.samples[1].name = sample_name_1

    # WHEN validating that the sample names are unique
    errors = validate_sample_names_unique(valid_microsalt_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the repeated sample name
    assert isinstance(errors[0], SampleNameRepeatedError)
