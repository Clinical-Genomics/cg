"""
Module to test the store_order_data_in_status_db method of the StoreFastqOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from cg.constants import DataDelivery, Workflow
from cg.services.orders.storing.implementations.fastq_order_service import StoreFastqOrderService
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store


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

    # THEN it should create one case per sample and one MAF case
    cases: list[Case] = store_to_submit_and_validate_orders._get_query(table=Case).all()
    assert len(cases) == 2
    links: list[CaseSample] = store_to_submit_and_validate_orders._get_query(table=CaseSample).all()
    assert len(links) == 2
    assert cases[0].data_analysis == Workflow.RAW_DATA
    assert cases[1].data_analysis == Workflow.RAW_DATA

    # THEN the analysis case has allowed data deliveries
    assert cases[1].data_delivery in [DataDelivery.FASTQ, DataDelivery.NO_DELIVERY]

    # THEN the sample sex should be stored
    assert db_samples[0].sex == "male"
