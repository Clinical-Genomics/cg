from cg.store import Store
from cg.store.models import Customer
from cg.store.filters.status_customer_filters import filter_customer_by_customer_internal_id


def test_filter_customer_by_customer_id(base_store: Store, customer_id: str):
    """Test return customer by customer internal id."""
    # GIVEN a store containing customers

    # WHEN retrieving a customer
    customer: Customer = filter_customer_by_customer_internal_id(
        customers=base_store._get_query(table=Customer),
        customer_id=customer_id,
    ).first()

    # THEN a customer should be returned
    assert customer

    # THEN the internal id should match the original
    assert customer.internal_id == customer_id
