from cg.constants import Sex
from cg.models.orders.sample_base import StatusEnum
from cg.services.orders.validation.errors.case_errors import (
    InvalidGenePanelsError,
    RepeatedGenePanelsError,
)
from cg.services.orders.validation.errors.case_sample_errors import (
    DescendantAsFatherError,
    FatherNotInCaseError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    PedigreeError,
    SampleIsOwnFatherError,
)
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.rules.case.rules import validate_gene_panels_unique
from cg.services.orders.validation.rules.case_sample.rules import (
    validate_fathers_are_male,
    validate_fathers_in_same_case_as_children,
    validate_gene_panels_exist,
    validate_mothers_are_female,
    validate_pedigree,
)
from cg.services.orders.validation.workflows.tomte.models.order import TomteOrder
from cg.store.models import Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


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


def test_father_must_be_male(order_with_invalid_father_sex: TomteOrder, base_store: Store):
    # GIVEN an order with an incorrectly specified father

    # WHEN validating the order
    errors: list[InvalidFatherSexError] = validate_fathers_are_male(
        order=order_with_invalid_father_sex, store=base_store
    )

    # THEN errors are returned
    assert errors

    # THEN the errors are about the father sex
    assert isinstance(errors[0], InvalidFatherSexError)


def test_existing_father_must_be_male(
    valid_order: TomteOrder, store_with_multiple_cases_and_samples: Store
):
    """Tests that an order with a father which is a female sample in StatusDB gives an error."""

    # GIVEN a sample in StatusDB with female sex
    father_db_sample: Sample = store_with_multiple_cases_and_samples.session.query(Sample).first()
    father_db_sample.sex = Sex.FEMALE
    store_with_multiple_cases_and_samples.commit_to_store()

    # GIVEN that an order has a corresponding existing sample in one of its cases
    father_sample = ExistingSample(internal_id=father_db_sample.internal_id)
    valid_order.cases[0].samples.append(father_sample)

    # GIVEN that another sample in the order specifies the sample as its father
    father_name = father_db_sample.name
    valid_order.cases[0].samples[0].father = father_name

    # WHEN validating the order
    errors: list[InvalidFatherSexError] = validate_fathers_are_male(
        order=valid_order, store=store_with_multiple_cases_and_samples
    )

    # THEN errors are returned
    assert errors

    # THEN the errors are about the father's sex
    assert isinstance(errors[0], InvalidFatherSexError)


def test_existing_mother_must_be_female(
    valid_order: TomteOrder, store_with_multiple_cases_and_samples: Store
):
    """Tests that an order with a mother which is a male sample in StatusDB gives an error."""

    # GIVEN a sample in StatusDB with male sex
    mother_db_sample: Sample = store_with_multiple_cases_and_samples.session.query(Sample).first()
    mother_db_sample.sex = Sex.MALE
    store_with_multiple_cases_and_samples.commit_to_store()

    # GIVEN that an order has a corresponding existing sample in one of its cases
    mother_sample = ExistingSample(internal_id=mother_db_sample.internal_id)
    valid_order.cases[0].samples.append(mother_sample)

    # GIVEN that another sample in the order specifies the sample as its mother
    mother_name = mother_db_sample.name
    valid_order.cases[0].samples[0].mother = mother_name

    # WHEN validating the order
    errors: list[InvalidMotherSexError] = validate_mothers_are_female(
        order=valid_order, store=store_with_multiple_cases_and_samples
    )

    # THEN errors are returned
    assert errors

    # THEN the errors are about the mother's sex
    assert isinstance(errors[0], InvalidMotherSexError)


def test_father_in_wrong_case(order_with_father_in_wrong_case: TomteOrder, base_store: Store):

    # GIVEN an order with the father sample in the wrong case

    # WHEN validating the order
    errors: list[FatherNotInCaseError] = validate_fathers_in_same_case_as_children(
        order=order_with_father_in_wrong_case, store=base_store
    )

    # THEN an error is returned
    assert errors

    # THEN the error is about the father being in the wrong case
    assert isinstance(errors[0], FatherNotInCaseError)


def test_sample_cannot_be_its_own_father(valid_order: TomteOrder, base_store: Store):
    # GIVEN an order with a sample which has itself as a parent
    sample = valid_order.cases[0].samples[0]
    sample.father = sample.name

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(order=valid_order, store=base_store)

    # THEN an error is returned
    assert errors

    # THEN the error is about the sample having itself as a parent
    assert isinstance(errors[0], SampleIsOwnFatherError)


def test_sample_cycle_not_allowed(order_with_sample_cycle: TomteOrder, base_store: Store):
    # GIVEN an order where a sample is a descendant of itself

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(order=order_with_sample_cycle, store=base_store)

    # THEN an error is returned
    assert errors

    # THEN the error is about the sample being a descendant of itself
    assert isinstance(errors[0], DescendantAsFatherError)


def test_incest_is_allowed(order_with_siblings_as_parents: TomteOrder, base_store: Store):
    # GIVEN an order where parents are siblings

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(
        order=order_with_siblings_as_parents, store=base_store
    )

    # THEN no error is returned
    assert not errors


def test_existing_samples_in_tree(
    valid_order: TomteOrder, base_store: Store, helpers: StoreHelpers
):
    # GIVEN a valid order where an existing sample is added
    sample = helpers.add_sample(store=base_store)
    existing_sample = ExistingSample(internal_id=sample.internal_id, status=StatusEnum.affected)
    valid_order.cases[0].samples.append(existing_sample)

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(order=valid_order, store=base_store)

    # THEN no error is returned
    assert not errors


def test_existing_sample_cycle_not_allowed(
    order_with_existing_sample_cycle: TomteOrder, base_store: Store, helpers: StoreHelpers
):

    # GIVEN an order containing an existing sample and a cycle
    existing_sample = order_with_existing_sample_cycle.cases[0].samples[1]
    assert not existing_sample.is_new
    helpers.add_sample(
        store=base_store, name="ExistingSampleName", internal_id=existing_sample.internal_id
    )

    # WHEN validating the order
    errors: list[PedigreeError] = validate_pedigree(
        order=order_with_existing_sample_cycle, store=base_store
    )

    # THEN an error is returned
    assert errors

    # THEN the error is about the sample being a descendant of itself
    assert isinstance(errors[0], DescendantAsFatherError)
