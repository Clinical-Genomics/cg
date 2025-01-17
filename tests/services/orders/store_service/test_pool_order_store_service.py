import pytest

from cg.constants import Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.orders.storing.implementations.pool_order_service import StorePoolOrderService
from cg.services.orders.validation.models.order_aliases import OrderWithIndexedSamples
from cg.store.models import ApplicationVersion, Case, CaseSample, Order, Pool, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "order_fixture, workflow",
    [("rml_order", Workflow.RAW_DATA), ("fluffy_order", Workflow.FLUFFY)],
    ids=["RML", "Fluffy"],
)
def test_store_order_data_in_status_db(
    store_with_rml_applications: Store,
    order_fixture: str,
    ticket_id: str,
    store_pool_order_service: StorePoolOrderService,
    workflow: Workflow,
    request: pytest.FixtureRequest,
):
    """Test that a Fluffy or RML order is stored in the database."""
    # GIVEN a valid Fluffy or RML order
    order: OrderWithIndexedSamples = request.getfixturevalue(order_fixture)

    # GIVEN a store with no samples, pools, cases nor orders
    assert store_with_rml_applications._get_query(table=Sample).count() == 0
    assert store_with_rml_applications._get_query(table=Pool).count() == 0
    assert store_with_rml_applications._get_query(table=Case).count() == 0
    assert store_with_rml_applications._get_query(table=CaseSample).count() == 0
    assert store_with_rml_applications._get_query(table=Order).count() == 0

    # GIVEN that the store has application versions for the RML workflow
    apps: list[ApplicationVersion] = store_with_rml_applications._get_query(
        table=ApplicationVersion
    ).all()
    assert len(apps) == 4
    for app in apps:
        assert app.application.prep_category == SeqLibraryPrepCategory.READY_MADE_LIBRARY

    # WHEN storing the order
    new_pools: list[Pool] = store_pool_order_service.store_order_data_in_status_db(order=order)

    # THEN it should return the pools
    assert len(new_pools) == 4
    assert isinstance(new_pools[0], Pool)

    # THEN the pools should be stored in the database
    db_pools: list[Pool] = store_with_rml_applications._get_query(table=Pool).all()
    assert len(db_pools) == 4
    assert set(new_pools) == set(db_pools)

    # THEN the database pools should be invoiced, have a RML application and the correct ticket id
    for pool in db_pools:
        assert not pool.no_invoice
        assert pool.application_version.application.tag.startswith("RML")
        assert pool.ticket == ticket_id

    # THEN the order should be stored, have the correct ticket id
    new_order = store_with_rml_applications._get_query(table=Order).first()
    assert new_order.ticket_id == int(ticket_id)

    # THEN it should store the samples and create a case for each sample
    new_samples: list[Sample] = store_with_rml_applications._get_query(table=Sample).all()
    new_cases: list[Case] = store_with_rml_applications._get_query(table=Case).all()
    assert len(new_samples) == 4
    assert len(new_cases) == 4
    assert store_with_rml_applications._get_query(table=CaseSample).count() == 4

    # THEN the samples are not set for invoicing
    for sample in new_samples:
        assert sample.no_invoice

    # THEN the cases should have the correct data analysis
    for case in new_cases:
        assert case.data_analysis == workflow
