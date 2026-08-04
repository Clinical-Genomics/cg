import pytest

from cg.exc import OrderNotFoundError
from cg.store.models import Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_order_by_ticket_id_strict_success(store: Store, helpers: StoreHelpers):
    # GIVEN a store with two orders with different ticket IDs
    order_1: Order = store.add_order(
        ticket_id=123,
        customer=helpers.ensure_customer(store),
    )
    order_2: Order = store.add_order(
        ticket_id=456,
        customer=helpers.ensure_customer(store),
    )
    store.add_multiple_items_to_store([order_1, order_2])

    # WHEN fetching an order by ticket ID
    fetched_order: Order = store.get_order_by_ticket_id_strict(123)

    # THEN it should return the correct order
    assert fetched_order == order_1


def test_get_order_by_ticket_id_strict_not_found(store: Store):
    # GIVEN an empty store

    # WHEN fetching an order by a ticket ID that does not exist
    # THEN it should raise an OrderNotFoundError
    with pytest.raises(OrderNotFoundError):
        store.get_order_by_ticket_id_strict(999)
