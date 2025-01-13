from cg.services.order_validation_service.errors.sample_errors import MutantSampleNameNotUniqueError
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.mutant.rules import (
    validate_non_control_samples_are_unique,
)


def test_validate_non_control_samples_are_unique(
    mutant_order_control_sample_same_name: MutantOrder,
):
    """
    Test that an order with a control sample with the same name as a non-control sample does not
    return any exception.
    """
    # GIVEN a mutant order with a control sample with the same name as a non-control sample

    # WHEN validating the order
    errors = validate_non_control_samples_are_unique(mutant_order_control_sample_same_name)

    # THEN no errors should be returned
    assert not errors


def test_test_validate_non_control_samples_are_not_unique(
    mutant_order_with_samples_with_same_name: MutantOrder,
):
    """Test that an order with non-control samples with the same name returns an error."""
    # GIVEN a mutant order with two non-control samples with the same name

    # WHEN validating the order
    errors = validate_non_control_samples_are_unique(mutant_order_with_samples_with_same_name)

    # THEN errors should be returned
    assert errors

    # THEN there should be one error per non-control sample with a non-unique name
    assert len(errors) == 2

    # THEN the errors should be of the correct type
    assert isinstance(errors[0], MutantSampleNameNotUniqueError)
