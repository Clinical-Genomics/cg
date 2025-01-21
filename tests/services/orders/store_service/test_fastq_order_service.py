"""
Module to test the store_order_data_in_status_db method of the StoreFastqOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from cg.constants import DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.orders.storing.constants import MAF_ORDER_ID
from cg.services.orders.storing.implementations.fastq_order_service import StoreFastqOrderService
from cg.services.orders.validation.workflows.fastq.models.order import FastqOrder
from cg.store.models import Application, Case, Order, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_store_order_data_in_status_db(
    store_to_submit_and_validate_orders: Store,
    store_fastq_order_service: StoreFastqOrderService,
    fastq_order: FastqOrder,
    ticket_id_as_int: int,
):
    """Test that a Fastq order with two WGS samples, one being tumour, is stored in the database."""

    # GIVEN a fastq order with two WGS samples, the first one being a tumour sample

    # GIVEN a basic store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples: list[Sample] = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN it should store the order
    assert store_to_submit_and_validate_orders.get_order_by_ticket_id(ticket_id_as_int)

    # THEN it should store the samples
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)

    # THEN it should create one case for the analysis and one MAF case
    cases: list[Case] = store_to_submit_and_validate_orders._get_query(table=Case).all()
    assert len(cases) == 2
    assert len(db_samples[0].links) == 2
    assert cases[0].data_analysis == Workflow.MIP_DNA
    assert cases[1].data_analysis == Workflow.RAW_DATA

    # THEN the analysis case has allowed data deliveries
    assert cases[1].data_delivery in [DataDelivery.FASTQ, DataDelivery.NO_DELIVERY]

    # THEN the sample sex should be stored
    assert db_samples[0].sex == "male"

    # THEN the MAF order should have one case linked to the tumour negative sample
    maf_order: Order = store_to_submit_and_validate_orders.get_order_by_id(MAF_ORDER_ID)
    maf_cases: list[Case] = maf_order.cases
    assert len(maf_cases) == 1
    assert not maf_cases[0].samples[0].is_tumour


def test_store_fastq_samples_non_tumour_wgs_to_mip_maf_case(
    store_to_submit_and_validate_orders: Store,
    fastq_order: FastqOrder,
    store_fastq_order_service: StoreFastqOrderService,
):
    """Test that a non-tumour WGS sample creates a MAF case with MIP as data analysis."""
    # GIVEN a basic store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0

    # GIVEN a fastq order with the first sample being a non-tumour WGS sample
    store_to_submit_and_validate_orders.get_application_by_tag(
        fastq_order.samples[0].application
    ).prep_category = SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    fastq_order.samples[0].tumour = False

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN a MAF case was created for the first sample
    assert new_samples[0].links[0].case.data_analysis == Workflow.MIP_DNA

    # THEN the case for the analysis is also created
    assert new_samples[0].links[1].case.data_analysis == Workflow.RAW_DATA


def test_store_fastq_samples_tumour_wgs_to_fastq_no_maf_case(
    store_to_submit_and_validate_orders: Store,
    fastq_order: FastqOrder,
    store_fastq_order_service: StoreFastqOrderService,
):
    """Test that a tumour WGS sample does not create MAF cases."""
    # GIVEN a basic store with no samples
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0

    # GIVEN a fastq order with the second sample being a tumour WGS sample
    store_to_submit_and_validate_orders.get_application_by_tag(
        fastq_order.samples[0].application
    ).prep_category = SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    fastq_order.samples[1].tumour = True

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN only one case is linked to the second sample
    assert len(new_samples[1].links) == 1

    # THEN the data analysis for the case should be RAW_DATA
    assert new_samples[1].links[0].case.data_analysis == Workflow.RAW_DATA


def test_store_fastq_samples_non_wgs_no_maf_case(
    store_to_submit_and_validate_orders: Store,
    fastq_order: FastqOrder,
    store_fastq_order_service: StoreFastqOrderService,
    helpers: StoreHelpers,
):
    """Test that an order with non-WGS samples creates no MAF cases."""
    # GIVEN a basic store with no samples
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0

    # GIVEN that the store has application versions for the non-WGS workflow
    non_wgs_prep_category = SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
    helpers.ensure_application_version(
        store=store_to_submit_and_validate_orders, prep_category=non_wgs_prep_category
    )

    # GIVEN a fastq order with a non-WGS samples
    non_wgs_applications: Application = store_to_submit_and_validate_orders._get_query(
        table=Application
    ).filter(Application.prep_category == non_wgs_prep_category)
    assert non_wgs_applications
    for sample in fastq_order.samples:
        sample.application = non_wgs_applications[0].tag

    # WHEN storing the order
    new_samples = store_fastq_order_service.store_order_data_in_status_db(fastq_order)

    # THEN only one case is linked to the sample
    assert len(new_samples[0].links) == 1

    # THEN the data analysis for the case should be RAW_DATA
    assert new_samples[0].links[0].case.data_analysis == Workflow.RAW_DATA
