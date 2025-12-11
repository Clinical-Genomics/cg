from cg.constants import GenePanelMasterList
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, SexEnum, StatusEnum
from cg.services.orders.validation.errors.case_errors import (
    CaseDoesNotExistError,
    CaseNameNotAvailableError,
    CaseOutsideOfCollaborationError,
    ExistingCaseWithoutAffectedSampleError,
    MultiplePrepCategoriesError,
    MultipleSamplesInCaseError,
    NewCaseWithoutAffectedSampleError,
    RepeatedCaseNameError,
)
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.balsamic.constants import BalsamicDeliveryType
from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.order_types.mip_dna.models.order import MIPDNAOrder
from cg.services.orders.validation.order_types.rna_fusion.models.order import RNAFusionOrder
from cg.services.orders.validation.order_types.rna_fusion.models.sample import RNAFusionSample
from cg.services.orders.validation.rules.case.rules import (
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
    validate_each_new_case_has_an_affected_sample,
    validate_existing_cases_belong_to_collaboration,
    validate_existing_cases_have_an_affected_sample,
    validate_one_sample_per_case,
    validate_samples_in_case_have_same_bed_version,
    validate_samples_in_case_have_same_prep_category,
)
from cg.store.models import Application, Case
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
        container_name="container-name",
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


def test_new_case_without_affected_samples(mip_dna_order: MIPDNAOrder):
    """Tests that an error is returned if a new case does not contain any affected samples."""

    # GIVEN an order containing a case without any affected samples
    for sample in mip_dna_order.cases[0].samples:
        sample.status = StatusEnum.unaffected

    # WHEN validating that each case contains at least one affected sample
    errors: list[NewCaseWithoutAffectedSampleError] = validate_each_new_case_has_an_affected_sample(
        mip_dna_order
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the first case
    assert errors[0].case_index == 0


def test_existing_case_without_affected_samples(
    mip_dna_order: MIPDNAOrder,
    store_with_multiple_cases_and_samples: Store,
    case_id_with_single_sample: str,
):
    """Tests that an error is returned if an existing case does not contain any affected samples."""

    # GIVEN an order containing an existing case without any affected samples
    db_case: Case = store_with_multiple_cases_and_samples.get_case_by_internal_id(
        case_id_with_single_sample
    )
    assert all(link.status != StatusEnum.affected for link in db_case.links)
    existing_case = ExistingCase(internal_id=db_case.internal_id, panels=db_case.panels)
    mip_dna_order.cases.append(existing_case)

    # WHEN validating that each case contains at least one affected sample
    errors: list[ExistingCaseWithoutAffectedSampleError] = (
        validate_existing_cases_have_an_affected_sample(
            order=mip_dna_order, store=store_with_multiple_cases_and_samples
        )
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the first case
    assert errors[0].case_index == mip_dna_order.cases.index(existing_case)


def test_case_samples_multiple_prep_categories(
    mip_dna_order: MIPDNAOrder,
    store_to_submit_and_validate_orders: Store,
):
    # GIVEN a store with two applications from different prep categories
    store = store_to_submit_and_validate_orders
    wes_application: Application = store.get_application_by_tag("EXOKTTR040")
    wes_application.prep_category = "wes"
    wgs_application: Application = store.get_application_by_tag("WGSPCFC030")

    # GIVEN an order with a case containing samples with different prep categories
    mip_dna_order.cases[0].samples[0].application = wes_application.tag
    mip_dna_order.cases[0].samples[1].application = wgs_application.tag

    # WHEN validating that the case does not contain samples with different prep categories
    errors: list[MultiplePrepCategoriesError] = validate_samples_in_case_have_same_prep_category(
        order=mip_dna_order, store=store_to_submit_and_validate_orders
    )

    # THEN the expected error should be returned
    error = errors[0]
    assert isinstance(error, MultiplePrepCategoriesError)

    # THEN the error should concern the first case
    assert error.case_index == 0


def test_case_samples_have_different_bed_versions():
    # GIVEN a Balsamic order
    balsamic_order = BalsamicOrder(
        cases=[
            BalsamicCase(
                name="BalsamicCase1",
                samples=[
                    BalsamicSample(
                        application="PANKTTR060",
                        capture_kit="capture_kit1",
                        container=ContainerEnum.tube,
                        name="sample1",
                        sex=SexEnum.male,
                        source="blood",
                        subject_id="subjectID",
                    ),
                    BalsamicSample(
                        application="PANKTTR060",
                        capture_kit="capture_kit2",
                        container=ContainerEnum.tube,
                        name="sample2",
                        sex=SexEnum.male,
                        source="blood",
                        subject_id="subjectID",
                    ),
                ],
            ),
        ],
        customer="cust000",
        delivery_type=BalsamicDeliveryType.SCOUT,
        name="BalsamicOrder1",
        project_type=OrderType.BALSAMIC,
    )

    # WHEN validating that samples in a case have the same bed version
    validate_samples_in_case_have_same_bed_version(balsamic_order)
