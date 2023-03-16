from alchy import Query
from typing import List
from cg.store import Store
from cg.store.models import Pool
from tests.store_helpers import StoreHelpers
from cg.constants.invoice import CustomerNames
from cg.store.filters.status_pool_filters import (
    filter_pools_is_received,
    filter_pools_is_not_received,
    filter_pools_is_delivered,
    filter_pools_is_not_delivered,
    filter_pools_without_invoice_id,
    filter_pools_do_invoice,
    filter_pools_do_not_invoice,
    filter_pools_by_invoice_id,
    filter_pools_by_order_enquiry,
    filter_pools_by_name_enquiry,
    filter_pools_by_customer_id,
)
from datetime import datetime
from tests.store.conftest import StoreConftestFixture


def test_filter_pools_is_delivered(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a delivered pool."""

    # GIVEN a store with two pools of which one is delivered

    # WHEN getting delivered pools
    pools: Query = filter_pools_is_delivered(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_is_not_delivered(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITHOUT_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool that is not delivered."""

    # GIVEN a store with two pools of which one is delivered

    # WHEN getting not delivered pools
    pools: Query = filter_pools_is_not_delivered(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_is_received(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a received pool."""

    # GIVEN a store with two pools of which one is received

    # WHEN getting received pools
    pools: Query = filter_pools_is_received(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_is_not_received(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITHOUT_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool that is not received."""

    # GIVEN a store with two pools of which one is received

    # WHEN getting received pools
    pools: Query = filter_pools_is_not_received(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_do_not_invoice(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITHOUT_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool that should not be invoiced."""

    # GIVEN a pool marked to skip invoicing and one not marked to skip invoicing

    # WHEN getting pools marked to skip invoicing
    pools: Query = filter_pools_do_not_invoice(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_do_invoice(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool that should be invoiced."""

    # GIVEN a pool marked for invoicing and one not marked for invoicing

    # WHEN getting pools marked for invoicing
    pools: Query = filter_pools_do_invoice(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_by_invoice_id(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
    invoice_id=StoreConftestFixture.INVOICE_ID_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool with a specific invoice id."""

    # GIVEN a store with two pools of which one us marked for invoicing

    # WHEN getting pools with invoice_id
    pools: Query = filter_pools_by_invoice_id(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool),
        invoice_id=invoice_id,
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_without_invoice_id(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITHOUT_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool without invoice id."""

    # GIVEN a store with two pools of which one has no invoice id

    # WHEN getting pools without invoice_id
    pools: Query = filter_pools_without_invoice_id(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool)
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1


def test_filter_pools_by_name_enquiry(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool with a specific name enquiry."""

    # GIVEN a store with two pools of which one has a name enquiry

    # WHEN getting pools with name enquiry
    pools: Query = filter_pools_by_name_enquiry(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool),
        name_enquiry=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_by_order_enquiry(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool with a specific order enquiry."""

    # GIVEN a store with two pools of which one has an order enquiry

    # WHEN getting pools with order enquiry
    pools: Query = filter_pools_by_order_enquiry(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool),
        order_enquiry=StoreConftestFixture.ORDER_POOL_WITH_ATTRIBUTES.value,
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 1 and pools.all()[0].name == name


def test_filter_pools_by_customer_id(
    store_with_a_pool_with_and_without_attributes: Store,
    name=StoreConftestFixture.NAME_POOL_WITH_ATTRIBUTES.value,
):
    """Test that a pool is returned when there is a pool with a specific customer id."""

    # GIVEN a store with two pools of which one has a customer id

    # WHEN getting pools with customer id
    pools: Query = filter_pools_by_customer_id(
        pools=store_with_a_pool_with_and_without_attributes._get_query(table=Pool),
        customer_ids=[1],
    )

    # ASSERT that the query is a Query
    assert isinstance(pools, Query)

    # THEN pools should contain the test pool
    assert pools.all() and len(pools.all()) == 2 and pools.all()[0].name == name
