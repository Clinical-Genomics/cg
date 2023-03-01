from alchy import Query
from typing import List
from cg.store import Store
from tests.store_helpers import StoreHelpers
from cg.store.status_pool_filters import (
    get_pool_is_received,
    get_pool_is_not_received,
    get_pool_is_delivered,
    get_pool_is_not_delivered,
    get_pool_without_invoice_id,
    get_pool_do_invoice,
    get_pool_do_not_invoice,
    get_pool_by_invoice_id,
)
from datetime import datetime


def test_filter_pool_is_delivered(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a pool is returned when there is a delivered pool."""

    # GIVEN a delivered pool
    helpers.ensure_pool(base_store, delivered_at=datetime.now(), name="delivered")
    helpers.ensure_pool(base_store, delivered_at=None, name="not_delivered")

    # ASSERT that there are really two pools
    assert base_store._get_pool_query().count() == 2
    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered pools
    pools: List[Query] = list(get_pool_is_delivered(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_is_not_delivered(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a pool is returned when there is a pool that is not delivered."""

    # GIVEN a not delivered pool
    helpers.ensure_pool(base_store, delivered_at=datetime.now(), name="delivered")
    helpers.ensure_pool(base_store, delivered_at=None, name="not_delivered")

    # ASSERT that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # GIVEN a pool Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting not delivered pools
    pools: List[Query] = list(get_pool_is_not_delivered(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_is_received(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a pool is returned when there is a received pool."""

    # GIVEN a received pool
    helpers.ensure_pool(base_store, received_at=datetime.now(), name="received")
    helpers.ensure_pool(base_store, received_at=None, name="not_received")

    # GIVEN a pool Query
    pools: Query = base_store._get_pool_query()

    # ASSERT that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # WHEN getting received pools
    pools: List[Query] = list(get_pool_is_received(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_is_not_received(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a pool is returned when there is a pool that is not received."""

    # GIVEN a not received pool
    helpers.ensure_pool(base_store, received_at=None, name="not_received")
    helpers.ensure_pool(base_store, received_at=datetime.now(), name="received")

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # ASSERT that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # WHEN getting not received pools
    pools: List[Query] = list(get_pool_is_not_received(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_do_invoice(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a pool is returned when there is a pool that should be invoiced."""

    # GIVEN a pool marked for invoicing and one not marked for invoicing
    helpers.ensure_pool(base_store, no_invoice=False, name="invoice")
    helpers.ensure_pool(base_store, no_invoice=True, name="no_invoice")

    # ASSERT that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting pools marked for invoicing
    pools: List[Query] = list(get_pool_do_invoice(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_do_not_invoice(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a pool is returned when there is a pool that should not be invoiced."""

    # GIVEN a pool marked to skip invoicing.
    helpers.ensure_pool(base_store, no_invoice=True, name="no_invoice")
    helpers.ensure_pool(base_store, no_invoice=False, name="invoice")

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # ASSERT that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # WHEN getting pools marked to skip invoicing
    pools: List[Query] = list(get_pool_do_not_invoice(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_by_invoice_id(base_store: Store, helpers: StoreHelpers, invoice_id=5):
    """Test that a pool is returned when there is a pool with a specific invoice id."""

    # GIVEN a pool with invoice_id
    helpers.ensure_pool(base_store, invoice_id=invoice_id, name="invoice_id")
    helpers.ensure_pool(base_store, invoice_id=None, name="no_invoice_id")

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # assert that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # WHEN getting pools with invoice_id
    pools: List[Query] = list(get_pool_by_invoice_id(pools=pools, invoice_id=invoice_id))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1


def test_filter_pool_without_invoice_id(
    base_store: Store,
    helpers: StoreHelpers,
    invoice_id=5,
):
    """Test that a pool is returned when there is a pool without invoice id."""

    # GIVEN a pool without invoice_id
    helpers.ensure_pool(base_store, invoice_id=None, name="no_invoice_id")
    helpers.ensure_pool(base_store, invoice_id=invoice_id, name="invoice_id")

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # assert that there are really two pools
    assert base_store._get_pool_query().count() == 2

    # WHEN getting pools without invoice_id
    pools: List[Query] = list(get_pool_without_invoice_id(pools=pools))

    # THEN pools should contain the test pool
    assert pools and len(pools) == 1
