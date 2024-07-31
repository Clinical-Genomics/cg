from cg.services.order_validation_service.models.errors import (
    FatherNotInCaseError,
    InvalidFatherSexError,
    InvalidPedigreeError,
    OccupiedWellError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.rules import (
    validate_fathers_are_male,
    validate_fathers_in_same_case_as_children,
    validate_no_repeated_case_names,
    validate_no_repeated_sample_names,
    validate_pedigree,
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


def test_repeated_sample_names_not_allowed(order_with_repeated_sample_names: TomteOrder):
    # Given an order with samples in a case with the same name

    # WHEN validating the order
    errors = validate_no_repeated_sample_names(order_with_repeated_sample_names)

    # THEN errors are returned
    assert errors

    # THEN the errors are about the sample names
    assert isinstance(errors[0], RepeatedSampleNameError)


def test_repeated_case_names_not_allowed(order_with_repeated_case_names: TomteOrder):
    # GIVEN an order with cases with the same name

    # WHEN validating the order
    errors = validate_no_repeated_case_names(order_with_repeated_case_names)

    # THEN errors are returned
    assert errors

    # THEN the errors are about the case names
    assert isinstance(errors[0], RepeatedCaseNameError)


def test_father_must_be_male(order_with_invalid_father_sex: TomteOrder):
    # GIVEN an order with an incorrectly specified father

    # WHEN validating the order
    errors = validate_fathers_are_male(order_with_invalid_father_sex)

    # THEN errors are returned
    assert errors

    # THEN the errors are about the father sex
    assert isinstance(errors[0], InvalidFatherSexError)


def test_no_father_sex_error_when_no_father_present(valid_order: TomteOrder):
    # GIVEN a valid order

    # WHEN validating the order
    errors = validate_fathers_are_male(valid_order)

    # THEN no errors are returned
    assert not errors


def test_father_in_wrong_case(order_with_father_in_wrong_case: TomteOrder):

    # GIVEN an order with the father sample in the wrong case

    # WHEN validating the order
    errors = validate_fathers_in_same_case_as_children(order_with_father_in_wrong_case)

    # THEN an error is returned
    assert errors

    # THEN the error is about the father being in the wrong case
    assert isinstance(errors[0], FatherNotInCaseError)


def test_invalid_pedigree_self_as_parent(valid_order: TomteOrder):
    # GIVEN an order with a sample which has itself as a parent
    sample = valid_order.cases[0].samples[0]
    sample.father = sample.name

    # WHEN validating the order
    errors = validate_pedigree(valid_order)

    # THEN an error is returned
    assert errors

    # THEN the error is about the sample having itself as a parent
    assert isinstance(errors[0], InvalidPedigreeError)
