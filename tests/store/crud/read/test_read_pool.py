from cg.store.models import Customer, Pool
from cg.store.store import Store


def test_get_pools_to_invoice_query(
    store_with_pools_for_multiple_customers: Store,
    three_pool_names: list[str],
):
    """Test return pools to invoice."""
    # GIVEN a store with multiple pools for multiple customers
    assert len(store_with_pools_for_multiple_customers.get_pools()) > 1

    # WHEN finding samples to invoice
    pools: list[Pool] = store_with_pools_for_multiple_customers.get_pools_to_invoice_query().all()

    # THEN it should return all pools that are not invoiced
    for pool in pools:
        assert pool.name in three_pool_names
        assert isinstance(pool, Pool)


def test_get_pools_to_invoice_for_customer(
    store_with_pools_for_multiple_customers: Store,
    three_customer_ids: list[str],
):
    """Test return pools to invoice for a customer."""
    # GIVEN a store with multiple pools for multiple customers
    assert len(store_with_pools_for_multiple_customers.get_pools()) > 1

    # THEN the one customer can be retrieved
    customer: Customer = store_with_pools_for_multiple_customers.get_customer_by_internal_id(
        customer_internal_id=three_customer_ids[1]
    )
    assert customer

    # WHEN finding samples to invoice for a customer
    pools: list[Pool] = store_with_pools_for_multiple_customers.get_pools_to_invoice_for_customer(
        customer=customer
    )

    # THEN it should return all pools that are not invoiced for the customer
    assert pools[0].customer == customer
