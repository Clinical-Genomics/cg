import datetime as dt
import pytest
from cg.exc import OrderError
from cg.models.orders.order import OrderIn, OrderType
from cg.services.orders.store_order_services.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.store.models import Sample
from cg.store.store import Store


def test_metagenome_to_status(
    metagenome_order_to_submit: dict, store_metagenome_order_service: StoreMetagenomeOrderService
):
    # GIVEN metagenome order with two samples
    order = OrderIn.parse_obj(metagenome_order_to_submit, OrderType.METAGENOME)

    # WHEN parsing for status
    data = store_metagenome_order_service.order_to_status(order=order)
    case = data["families"][0]
    # THEN it should pick out samples and relevant information
    assert len(case["samples"]) == 2
    first_sample = case["samples"][0]
    assert first_sample["name"] == "Bristol"
    assert first_sample["application"] == "METLIFR020"
    assert first_sample["priority"] == "standard"
    assert first_sample["volume"] == "1.0"


def test_store_metagenome_samples_bad_apptag(
    base_store: Store,
    metagenome_status_data: dict,
    ticket_id: str,
    store_metagenome_order_service: StoreMetagenomeOrderService,
):
    # GIVEN a basic store with no samples and a metagenome order
    assert not base_store._get_query(table=Sample).first()

    for sample in metagenome_status_data["families"][0]["samples"]:
        sample["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        store_metagenome_order_service.store_items_in_status(
            customer_id=metagenome_status_data["customer"],
            order=metagenome_status_data["order"],
            ordered=dt.datetime.now(),
            ticket_id=ticket_id,
            items=metagenome_status_data["families"],
        )
