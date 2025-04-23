import pytest

from cg.store.models import Customer, Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def delivery_message_store(
    store: Store,
    helpers: StoreHelpers,
    delivery_cases: list[dict],
    customer_id: str,
    ticket_id_as_int: int,
) -> Store:
    """Returns a store with test cases for the delivery message test suite."""
    customer: Customer = helpers.ensure_customer(store=store, customer_id=customer_id)
    order: Order = helpers.add_order(
        store=store, customer_id=customer.id, ticket_id=ticket_id_as_int
    )
    for case_dict in delivery_cases:
        helpers.ensure_case(store=store, customer=customer, order=order, **case_dict)
    return store
