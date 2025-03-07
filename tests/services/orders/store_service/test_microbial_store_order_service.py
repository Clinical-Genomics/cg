"""
Module to test the store_order_data_in_status_db method of the StoreMicrobialOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.models.orders.sample_base import ControlEnum
from cg.services.orders.storing.implementations.microbial_order_service import (
    StoreMicrobialOrderService,
)
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.store.models import Case, Organism, Sample
from cg.store.store import Store


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

    # THEN the control samples should have the correct control value
    positive: Sample = store_to_submit_and_validate_orders.get_sample_by_name("control-positive")
    assert positive.control == ControlEnum.positive
    negative: Sample = store_to_submit_and_validate_orders.get_sample_by_name("control-negative")
    assert negative.control == ControlEnum.negative
