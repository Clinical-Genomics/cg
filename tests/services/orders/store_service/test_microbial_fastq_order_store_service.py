from cg.constants import DataDelivery
from cg.services.orders.storing.implementations.microbial_fastq_order_service import (
    StoreMicrobialFastqOrderService,
)
from cg.services.orders.validation.workflows.microbial_fastq.models.order import MicrobialFastqOrder
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_store_samples(
    microbial_fastq_order: MicrobialFastqOrder,
    store_microbial_fastq_order_service: StoreMicrobialFastqOrderService,
):
    # GIVEN a microbial fastq order with microbial samples

    # GIVEN a basic store with no samples and a fastq order
    store: Store = store_microbial_fastq_order_service.status_db
    assert not store._get_query(table=Sample).first()
    assert store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples = store_microbial_fastq_order_service.store_order_data_in_status_db(
        order=microbial_fastq_order
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert len(store._get_query(table=Sample).all()) == 2
    assert store._get_query(table=Case).count() == 2
    first_sample = new_samples[0]
    assert len(first_sample.links) == 1
    case_link = first_sample.links[0]
    assert case_link.case in store.get_cases()
    assert case_link.case.data_analysis
    assert case_link.case.data_delivery == DataDelivery.FASTQ
