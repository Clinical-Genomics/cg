from cg.services.orders.storing.implementations.metagenome_order_service import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.validation.workflows.metagenome.models.order import MetagenomeOrder
from cg.store.models import Sample


def test_store_metagenome_samples(
    metagenome_order: MetagenomeOrder,
    store_metagenome_order_service: StoreMetagenomeOrderService,
):
    # GIVEN a basic store with no samples and a valid metagenome order with two samples

    # WHEN storing the order
    response: list[Sample] = store_metagenome_order_service.store_order_data_in_status_db(
        metagenome_order
    )

    # THEN the response should contain the two samples
    assert len(response) == 2
