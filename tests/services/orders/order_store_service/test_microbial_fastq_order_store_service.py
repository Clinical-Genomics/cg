from cg.constants import Workflow, DataDelivery
from cg.models.orders.order import OrderIn

from cg.models.orders.constants import OrderType
from cg.services.orders.store_order_services.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)


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
