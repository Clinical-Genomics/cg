"""Tests for the functions in the store api status related to the customer module."""

from cg.constants.constants import CustomerId
from cg.store.models import Customer
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_customers_to_invoice(
    store_with_samples_for_multiple_customers: Store,
    helpers: StoreHelpers,
    three_customer_ids: list[str],
):
    """Test that customers to invoice can be returned."""
    # GIVEN a database with samples for a customer

    # WHEN getting the customers to invoice
    customers: list[Customer] = store_with_samples_for_multiple_customers.get_customers_to_invoice(
        records=store_with_samples_for_multiple_customers.get_samples_to_invoice_query()
    )

    # THEN the customers should be returned
    assert customers
    assert len(customers) == 2
    for customer in customers:
        assert customer.internal_id in three_customer_ids

    # THEN the customers to invoice should not contain cust000
    for customer in customers:
        assert customer.internal_id != CustomerId.CG_INTERNAL_CUSTOMER
