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
)
from datetime import datetime


def test_filter_pool_is_delivered(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, delivered_at=datetime.now())

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_is_delivered(pools=pools))

    # THEN samples should contain the test sample
    assert pools


def test_filter_pool_is_not_delivered(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, delivered_at=None)

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_is_not_delivered(pools=pools))

    # THEN samples should contain the test sample
    assert pools


def test_filter_pool_is_received(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, received_at=datetime.now())

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_is_received(pools=pools))

    # THEN samples should contain the test sample
    assert pools


def test_filter_pool_is_not_received(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, received_at=None)

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_is_not_received(pools=pools))

    # THEN samples should contain the test sample
    assert pools


def test_filter_pool_do_invoice(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, no_invoice=False)

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_do_invoice(pools=pools))

    # THEN samples should contain the test sample
    assert pools


def test_filter_pool_do_not_invoice(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, no_invoice=True)

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_do_not_invoice(pools=pools))

    # THEN samples should contain the test sample
    assert pools


def test_filter_pool_without_invoice_id(
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.ensure_pool(base_store, invoice_id=None)

    # GIVEN a cases Query
    pools: Query = base_store._get_pool_query()

    # WHEN getting delivered samples
    pools: List[Query] = list(get_pool_without_invoice_id(pools=pools))

    # THEN samples should contain the test sample
    assert pools
