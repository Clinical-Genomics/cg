from cg.constants import GenePanelMasterList
from cg.models.orders.sample_base import ContainerEnum, SexEnum
from cg.services.orders.validation.errors.case_errors import (
    CaseDoesNotExistError,
    CaseNameNotAvailableError,
    CaseOutsideOfCollaborationError,
    MultipleSamplesInCaseError,
    RepeatedCaseNameError,
)
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.rules.case.rules import (
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
    validate_existing_cases_belong_to_collaboration,
    validate_one_sample_per_case,
)
from cg.services.orders.validation.workflows.mip_dna.models.order import MIPDNAOrder
from cg.services.orders.validation.workflows.rna_fusion.models.order import RNAFusionOrder
from cg.services.orders.validation.workflows.rna_fusion.models.sample import RNAFusionSample
from cg.store.models import Case
from cg.store.store import Store


def test_case_name_not_available(
    valid_order: OrderWithCases, store_with_multiple_cases_and_samples: Store
):
    store = store_with_multiple_cases_and_samples

    # GIVEN an order with a new case that has the same name as an existing case
    case: Case = store.get_cases()[0]
    valid_order.cases[0].name = case.name
    valid_order.customer = case.customer.internal_id

    # WHEN validating that the case name is available
    errors: list[CaseNameNotAvailableError] = validate_case_names_available(
        order=valid_order, store=store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the case name
    assert isinstance(errors[0], CaseNameNotAvailableError)


def test_case_internal_ids_does_not_exist(
    valid_order: OrderWithCases,
    store_with_multiple_cases_and_samples: Store,
):

    # GIVEN an order with a case marked as existing but which does not exist in the database
    existing_case = ExistingCase(internal_id="Non-existent case", panels=[GenePanelMasterList.AID])
    valid_order.cases.append(existing_case)

    # WHEN validating that the internal ids match existing cases
    errors: list[CaseDoesNotExistError] = validate_case_internal_ids_exist(
        order=valid_order,
        store=store_with_multiple_cases_and_samples,
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the non-existent case
    assert isinstance(errors[0], CaseDoesNotExistError)


def test_repeated_case_names_not_allowed(order_with_repeated_case_names: OrderWithCases):
    # GIVEN an order with cases with the same name

    # WHEN validating the order
    errors: list[RepeatedCaseNameError] = validate_case_names_not_repeated(
        order_with_repeated_case_names
    )

    # THEN errors are returned
    assert errors

    # THEN the errors are about the case names
    assert isinstance(errors[0], RepeatedCaseNameError)


def test_multiple_samples_in_case(rnafusion_order: RNAFusionOrder):
    # GIVEN an RNAFusion order with multiple samples in the same case
    rnafusion_sample = RNAFusionSample(
        container=ContainerEnum.tube,
        container_name="container_name",
        application="DummyAppTag",
        name="ExtraSample",
        require_qc_ok=False,
        sex=SexEnum.female,
        source="blood",
        subject_id="subject",
    )
    rnafusion_order.cases[0].samples.append(rnafusion_sample)

    # WHEN validating that the order has at most one sample per case
    errors: list[MultipleSamplesInCaseError] = validate_one_sample_per_case(rnafusion_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the multiple samples in the first case
    assert isinstance(errors[0], MultipleSamplesInCaseError)
    assert errors[0].case_index == 0


def test_case_outside_of_collaboration(
    mip_dna_order: MIPDNAOrder, store_with_multiple_cases_and_samples: Store
):

    # GIVEN a customer from outside the order's customer's collaboration
    new_customer = store_with_multiple_cases_and_samples.add_customer(
        internal_id="NewCustomer",
        name="New customer",
        invoice_address="Test street",
        invoice_reference="Invoice reference",
    )
    store_with_multiple_cases_and_samples.add_item_to_store(new_customer)
    store_with_multiple_cases_and_samples.commit_to_store()

    # GIVEN a case belonging to the customer is added to the order
    existing_cases: list[Case] = store_with_multiple_cases_and_samples.get_cases()
    case = existing_cases[0]
    case.customer = new_customer
    existing_case = ExistingCase(internal_id=case.internal_id, panels=case.panels)
    mip_dna_order.cases.append(existing_case)

    # WHEN validating that the order does not contain cases from outside the customer's collaboration
    errors: list[CaseOutsideOfCollaborationError] = validate_existing_cases_belong_to_collaboration(
        order=mip_dna_order, store=store_with_multiple_cases_and_samples
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the added existing case
    assert isinstance(errors[0], CaseOutsideOfCollaborationError)
