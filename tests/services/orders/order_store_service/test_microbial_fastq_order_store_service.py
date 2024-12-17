from cg.constants import DataDelivery
from cg.services.order_validation_service.workflows.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.orders.store_order_services.store_microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.store.models import Case, Sample


def test_store_samples(
    valid_microbial_fastq_order: MicrobialFastqOrder,
    store_microbial_fastq_order_service: StoreMicrobialFastqOrderService,
):
    # GIVEN a microbial fastq order with microbial samples

    # GIVEN a basic store with no samples and a fastq order
    assert not store_microbial_fastq_order_service.status_db._get_query(table=Sample).first()
    assert store_microbial_fastq_order_service.status_db._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_microbial_fastq_order_service.store_order_data_in_status_db(
        order=valid_microbial_fastq_order
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 3
    assert len(store_microbial_fastq_order_service.status_db._get_query(table=Sample).all()) == 3
    assert store_microbial_fastq_order_service.status_db._get_query(table=Case).count() == 3
    first_sample = new_samples[0]
    assert len(first_sample.links) == 1
    case_link = first_sample.links[0]
    assert case_link.case in store_microbial_fastq_order_service.status_db.get_cases()
    assert case_link.case.data_analysis
    assert case_link.case.data_delivery == DataDelivery.FASTQ
