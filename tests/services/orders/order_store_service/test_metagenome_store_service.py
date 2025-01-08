from cg.services.order_validation_service.workflows.metagenome.models.order import MetagenomeOrder
from cg.services.orders.store_order_services.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.store.models import Sample
from cg.store.store import Store


def test_store_metagenome_samples(
    base_store: Store,
    metagenome_order: MetagenomeOrder,
    ticket_id: str,
    store_metagenome_order_service: StoreMetagenomeOrderService,
):
    # GIVEN a basic store with no samples and a valid metagenome order with two samples

    # WHEN storing the order
    response: list[Sample] = store_metagenome_order_service.store_order_data_in_status_db(
        metagenome_order
    )

    # THEN the response should contain the two samples
    assert len(response) == 2
