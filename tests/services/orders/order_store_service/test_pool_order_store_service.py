import datetime as dt

import pytest

from cg.constants import DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.orders.order import OrderType
from cg.services.order_validation_service.workflows.fluffy.models.order import FluffyOrder
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder
from cg.services.orders.store_order_services.store_pool_order import StorePoolOrderService
from cg.store.models import ApplicationVersion, Case, CaseSample, Order, Pool, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_store_fluffy(
    store_with_rml_applications: Store,
    valid_fluffy_order: FluffyOrder,
    ticket_id: str,
    store_pool_order_service: StorePoolOrderService,
    helpers: StoreHelpers,
):
    # GIVEN a valid Fluffy order

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
    new_pools: list[Pool] = store_pool_order_service.store_order_data_in_status_db(
        order=valid_fluffy_order
    )

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
        assert case.data_analysis == Workflow.FLUFFY
