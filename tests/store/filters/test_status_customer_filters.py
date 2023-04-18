from cg.store import Store
from cg.store.models import Customer
from cg.store.filters.status_customer_filters import (
    filter_customer_by_customer_internal_id,
    filter_customer_by_exclude_customer_internal_id,
)

from sqlalchemy.orm import Query


def test_filter_customer_by_customer_id(base_store: Store, customer_id: str):
    """Test return customer by customer internal id."""
    # GIVEN a store containing customers

    # WHEN retrieving a customer
    customer: Customer = filter_customer_by_customer_internal_id(
        customers=base_store._get_query(table=Customer),
        customer_internal_id=customer_id,
    ).first()

    # THEN a customer should be returned
    assert customer

    # THEN the internal id should match the original
    assert customer.internal_id == customer_id


def test_filter_customer_by_exclude_customer_internal_id_exclude_one(
    store_with_cases_and_customers: Store,
):
    """Test that all customers except the one with the excluded internal ID are returned."""
    # GIVEN a store containing multiple customers
    customers_query: Query = store_with_cases_and_customers._get_query(table=Customer)
    exclude_internal_id = customers_query.first().internal_id

    # WHEN filtering customers by excluding a specific customer internal ID
    filtered_customers = filter_customer_by_exclude_customer_internal_id(
        customers=customers_query, exclude_customer_internal_id=exclude_internal_id
    )

    # THEN the query should return all customers except the one with the excluded internal ID
    assert filtered_customers.count() == (customers_query.count() - 1)
    for customer in filtered_customers:
        assert customer.internal_id != exclude_internal_id


def test_filter_customer_by_exclude_customer_internal_id_exclude_nonexistent(
    store_with_cases_and_customers: Store,
):
    """Test that all customers are returned when excluding a nonexistent internal ID."""
    # GIVEN a store containing multiple customers
    customers_query: Query = store_with_cases_and_customers._get_query(table=Customer)
    exclude_internal_id = "nonexistent_id"

    # WHEN filtering customers by excluding a nonexistent customer internal ID
    filtered_customers = filter_customer_by_exclude_customer_internal_id(
        customers=customers_query, exclude_customer_internal_id=exclude_internal_id
    )

    # THEN the query should return all customers
    assert filtered_customers.count() == customers_query.count()
