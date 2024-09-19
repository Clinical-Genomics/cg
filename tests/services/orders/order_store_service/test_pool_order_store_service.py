import datetime as dt

from cg.constants import DataDelivery, Workflow
from cg.models.orders.order import OrderIn, OrderType
from cg.services.orders.store_order_services.store_pool_order import StorePoolOrderService
from cg.store.models import Case, Pool, Sample
from cg.store.store import Store


def test_pools_to_status(
    rml_order_to_submit: dict, store_pool_order_service: StorePoolOrderService
):
    # GIVEN a rml order with three samples in one pool
    order = OrderIn.parse_obj(rml_order_to_submit, OrderType.RML)

    # WHEN parsing for status
    data = store_pool_order_service.order_to_status(order=order)

    # THEN it should pick out the general information
    assert data["customer"] == "cust000"
    assert data["order"] == "#123456"
    assert data["comment"] == "order comment"

    # ... and information about the pool(s)
    assert len(data["pools"]) == 2
    pool = data["pools"][0]
    assert pool["name"] == "pool-1"
    assert pool["application"] == "RMLP05R800"
    assert pool["data_analysis"] == Workflow.RAW_DATA
    assert pool["data_delivery"] == str(DataDelivery.FASTQ)
    assert len(pool["samples"]) == 2
    sample = pool["samples"][0]
    assert sample["name"] == "sample1"
    assert sample["comment"] == "test comment"
    assert pool["priority"] == "research"
    assert sample["control"] == "negative"


def test_store_rml(
    base_store: Store,
    rml_status_data: dict,
    ticket_id: str,
    store_pool_order_service: StorePoolOrderService,
):
    # GIVEN a basic store with no samples and a rml order
    assert base_store._get_query(table=Pool).count() == 0
    assert base_store._get_query(table=Case).count() == 0
    assert not base_store._get_query(table=Sample).first()

    # WHEN storing the order
    new_pools = store_pool_order_service.store_items_in_status(
        customer_id=rml_status_data["customer"],
        order=rml_status_data["order"],
        ordered=dt.datetime.now(),
        ticket_id=ticket_id,
        items=rml_status_data["pools"],
    )

    # THEN it should update the database with new pools
    assert len(new_pools) == 2

    assert base_store._get_query(table=Pool).count() == base_store._get_query(table=Case).count()
    assert len(base_store._get_query(table=Sample).all()) == 4

    # ASSERT that there is one negative sample
    negative_samples = 0
    for sample in base_store._get_query(table=Sample).all():
        if sample.control == "negative":
            negative_samples += 1
    assert negative_samples == 1

    new_pool = base_store._get_query(table=Pool).order_by(Pool.created_at.desc()).first()
    assert new_pool == new_pools[1]

    assert new_pool.name == "pool-2"
    assert new_pool.application_version.application.tag == "RMLP05R800"
    assert not hasattr(new_pool, "data_analysis")

    new_case = base_store.get_cases()[0]
    assert new_case.data_analysis == Workflow.RAW_DATA
    assert new_case.data_delivery == str(DataDelivery.FASTQ)

    # and that the pool is set for invoicing but not the samples of the pool
    assert not new_pool.no_invoice
    for link in new_case.links:
        assert link.sample.no_invoice
