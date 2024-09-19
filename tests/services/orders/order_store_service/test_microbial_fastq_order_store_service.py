from datetime import datetime

from cg.constants import DataDelivery, Workflow
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.services.orders.store_order_services.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.store.models import Case, Sample


def test_microbial_samples_to_status(
    microbial_fastq_order_to_submit: dict,
    store_microbial_fastq_order_service: StoreMicrobialFastqOrderService,
):
    # GIVEN microbial order with three samples
    order = OrderIn.parse_obj(microbial_fastq_order_to_submit, OrderType.MICROBIAL_FASTQ)

    # WHEN parsing for status
    data = store_microbial_fastq_order_service.order_to_status(order=order)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 2
    assert data["customer"] == "cust002"
    assert data["order"] == "Microbial Fastq order"
    assert data["comment"] == ""

    # THEN first sample should contain all the relevant data from the microbial order
    sample_data = data["samples"][0]
    assert sample_data["priority"] == "priority"
    assert sample_data["name"] == "prov1"
    assert sample_data.get("internal_id") is None
    assert sample_data["application"] == "WGSPCFC060"
    assert sample_data["comment"] == "sample comment"
    assert sample_data["volume"] == "1"
    assert sample_data["data_analysis"] == Workflow.MICROSALT
    assert sample_data["data_delivery"] == str(DataDelivery.FASTQ)


def test_store_samples(
    microbial_fastq_status_data: dict,
    ticket_id: str,
    store_microbial_fastq_order_service: StoreMicrobialFastqOrderService,
):
    # GIVEN a basic store with no samples and a fastq order

    assert not store_microbial_fastq_order_service.status_db._get_query(table=Sample).first()
    assert store_microbial_fastq_order_service.status_db._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_microbial_fastq_order_service.store_items_in_status(
        customer_id=microbial_fastq_status_data["customer"],
        order=microbial_fastq_status_data["order"],
        ordered=datetime.now(),
        ticket_id=ticket_id,
        items=microbial_fastq_status_data["samples"],
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert len(store_microbial_fastq_order_service.status_db._get_query(table=Sample).all()) == 2
    assert store_microbial_fastq_order_service.status_db._get_query(table=Case).count() == 2
    first_sample = new_samples[0]
    assert len(first_sample.links) == 1
    case_link = first_sample.links[0]
    assert case_link.case in store_microbial_fastq_order_service.status_db.get_cases()
    assert case_link.case.data_analysis
    assert case_link.case.data_delivery == DataDelivery.FASTQ
