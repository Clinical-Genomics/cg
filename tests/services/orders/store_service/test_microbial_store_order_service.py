"""
Module to test the store_order_data_in_status_db method of the StoreMicrobialOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from unittest.mock import Mock, create_autospec

import pytest

from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.models.orders.sample_base import ContainerEnum, ControlEnum, PriorityEnum
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.storing.implementations.microbial_order_service import (
    StoreMicrobialOrderService,
)
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.microsalt.models.sample import MicrosaltSample
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.store.models import Application, ApplicationVersion, Case, Customer, Organism, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_store_microsalt_order_data_in_status_db(
    store_to_submit_and_validate_orders: Store,
    microsalt_order: MicrosaltOrder,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a store with no samples nor cases
    assert store_to_submit_and_validate_orders._get_query(table=Sample).count() == 0
    assert not store_to_submit_and_validate_orders.get_cases()

    # GIVEN that the store has no organisms
    assert store_to_submit_and_validate_orders.get_all_organisms().count() == 0

    # WHEN storing the order
    new_samples: list[Sample] = store_microbial_order_service.store_order_data_in_status_db(
        microsalt_order
    )

    # THEN it should store the samples under a case
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)
    case_from_sample: Case = db_samples[0].links[0].case
    db_case: Case = store_to_submit_and_validate_orders.get_cases()[0]
    assert db_case == case_from_sample

    # THEN all case samples should be delivered
    for case_sample in db_case.links:
        assert case_sample.should_deliver_sample

    # THEN it should store the organisms
    assert store_to_submit_and_validate_orders.get_all_organisms().count() > 0

    # THEN the case should have the correct data analysis and data delivery
    assert db_case.data_analysis == Workflow.MICROSALT
    assert db_case.data_delivery == str(DataDelivery.FASTQ_QC_ANALYSIS)


def test_store_microbial_new_organism_in_status_db(
    store_to_submit_and_validate_orders: Store,
    microsalt_order: MicrosaltOrder,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    """Test that a new organism in a Microsalt order is stored in the status db."""
    # GIVEN a store with no organisms
    assert store_to_submit_and_validate_orders.get_all_organisms().count() == 0

    # GIVEN a Microsalt order with a new organism
    microsalt_order.samples[0].organism = "Canis lupus familiaris"
    microsalt_order.samples[0].reference_genome = "UU_Cfam_GSD_1.0"

    # WHEN storing the order
    store_microbial_order_service.store_order_data_in_status_db(microsalt_order)

    # THEN the organism should be stored in the status db
    organisms: list[Organism] = store_to_submit_and_validate_orders.get_all_organisms().all()
    dog: Organism = [
        organism for organism in organisms if organism.name == "Canis lupus familiaris"
    ][0]
    assert dog.reference_genome == "UU_Cfam_GSD_1.0"

    # THEN the organism should not be verified
    assert not dog.verified


def test_store_mutant_order_data_control_has_stored_value(
    mutant_order: MutantOrder,
    store_to_submit_and_validate_orders: Store,
    store_microbial_order_service: StoreMicrobialOrderService,
):
    # GIVEN a Mutant order with one positive and one negative control

    # GIVEN a store with no samples nor cases
    assert store_to_submit_and_validate_orders._get_query(table=Sample).count() == 0
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_samples: list[Sample] = store_microbial_order_service.store_order_data_in_status_db(
        mutant_order
    )

    # THEN it should store the samples under a case
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)
    case_from_sample: Case = db_samples[0].links[0].case
    db_case: Case = store_to_submit_and_validate_orders.get_cases()[0]
    assert db_case == case_from_sample

    # THEN all case samples should be delivered
    for case_sample in db_case.links:
        assert case_sample.should_deliver_sample

    # THEN the control samples should have the correct control value
    positive: Sample = store_to_submit_and_validate_orders.get_sample_by_name("control-positive")
    assert positive.control == ControlEnum.positive
    negative: Sample = store_to_submit_and_validate_orders.get_sample_by_name("control-negative")
    assert negative.control == ControlEnum.negative


@pytest.mark.parametrize(
    "is_external, expected_lims_status", [(True, LimsStatus.DONE), (False, LimsStatus.PENDING)]
)
def test_create_db_sample_with_lims_status(is_external: bool, expected_lims_status: LimsStatus):
    # GIVEN a store containing an external application
    application: Application = create_autospec(Application, is_external=is_external)
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_current_application_version_by_tag = Mock(
        return_value=application_version
    )
    customer: Customer = create_autospec(Customer)

    # GIVEN an order sample
    fastq_sample = MicrosaltSample(
        application="app",
        container=ContainerEnum.tube,
        elution_buffer=ElutionBuffer.OTHER,
        organism="Escherichia coli",
        priority=PriorityEnum.standard,
        name="sample",
        reference_genome="ref_genome",
    )

    # GIVEN a store case order service
    store_order_service = StoreMicrobialOrderService(
        status_db=status_db.as_type, lims_service=create_autospec(OrderLimsService)
    )

    # WHEN creating a db sample with the application
    store_order_service._create_db_sample(
        customer=customer,
        order_name="order",
        organism=create_autospec(Organism),
        sample=fastq_sample,
        ticket_id=1234567,
    )

    # THEN the sample should be created with LimsStatus DONE
    assert status_db.as_mock.add_sample.call_args[1]["lims_status"] == expected_lims_status
