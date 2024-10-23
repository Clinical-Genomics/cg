from cg.services.order_validation_service.errors.case_errors import (
    InvalidGenePanelsError,
    RepeatedGenePanelsError,
)
from cg.services.order_validation_service.errors.case_sample_errors import (
    DescendantAsFatherError,
    FatherNotInCaseError,
    InvalidFatherSexError,
    PedigreeError,
    SampleIsOwnFatherError,
)
from cg.services.order_validation_service.rules.case.rules import (
    validate_gene_panels_unique,
)
from cg.services.order_validation_service.rules.case_sample.rules import (
    validate_fathers_are_male,
    validate_fathers_in_same_case_as_children,
    validate_gene_panels_exist,
    validate_pedigree,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.store.store import Store


def test_invalid_gene_panels(valid_order: TomteOrder, base_store: Store):
    # GIVEN an order with an invalid gene panel specified
    invalid_panel = "Non-existent panel"
    valid_order.cases[0].panels = [invalid_panel]

    # WHEN validating that the gene panels exist
    errors: list[InvalidGenePanelsError] = validate_gene_panels_exist(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern invalid gene panels
    assert isinstance(errors[0], InvalidGenePanelsError)


def test_repeated_gene_panels(valid_order: TomteOrder, store_with_panels: Store):
    # GIVEN an order with repeated gene panels specified
    panel: str = store_with_panels.get_panels()[0].abbrev
    valid_order.cases[0].panels = [panel, panel]

    # WHEN validating that the gene panels are unique
    errors: list[RepeatedGenePanelsError] = validate_gene_panels_unique(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern repeated gene panels
    assert isinstance(errors[0], RepeatedGenePanelsError)


def test_father_must_be_male(order_with_invalid_father_sex: TomteOrder):
    # GIVEN an order with an incorrectly specified father

    # WHEN validating the order
    errors: list[InvalidFatherSexError] = validate_fathers_are_male(order_with_invalid_father_sex)

    # THEN errors are returned
    assert errors

    # THEN the errors are about the father sex
    assert isinstance(errors[0], InvalidFatherSexError)


def test_father_in_wrong_case(order_with_father_in_wrong_case: TomteOrder):

    # GIVEN an order with the father sample in the wrong case

    # WHEN validating the order
    errors: list[FatherNotInCaseError] = validate_fathers_in_same_case_as_children(
        order_with_father_in_wrong_case
    )

    # THEN an error is returned
    assert errors

    # THEN the error is about the father being in the wrong case
    assert isinstance(errors[0], FatherNotInCaseError)


def test_sample_cannot_be_its_own_father(valid_order: TomteOrder):
    # GIVEN an order with a sample which has itself as a parent
    sample = valid_order.cases[0].samples[0]
    sample.father = sample.name

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(valid_order)

    # THEN an error is returned
    assert errors

    # THEN the error is about the sample having itself as a parent
    assert isinstance(errors[0], SampleIsOwnFatherError)


def test_sample_cycle_not_allowed(order_with_sample_cycle: TomteOrder):
    # GIVEN an order where a sample is a descendant of itself

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(order_with_sample_cycle)

    # THEN an error is returned
    assert errors

    # THEN the error is about the sample being a descendant of itself
    assert isinstance(errors[0], DescendantAsFatherError)


def test_incest_is_allowed(order_with_siblings_as_parents: TomteOrder):
    # GIVEN an order where parents are siblings

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(order_with_siblings_as_parents)

    # THEN no error is returned
    assert not errors
