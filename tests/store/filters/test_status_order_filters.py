from sqlalchemy.orm import Query

from cg.constants import Workflow
from cg.store.filters.status_order_filters import filter_orders_by_ticket_id
from cg.store.models import Order
from cg.store.store import Store


def test_filter_orders_by_ticket_no_matching_ticket(base_store: Store, non_existent_id: str):
    """Test that no cases are returned when filtering by a non-existent ticket."""
    # GIVEN a store containing orders with no matching ticket id
    order = Order(
        id=1,
        customer_id=1,
        ticket_id=1,
    )
    base_store.session.add(order)
    base_store.session.commit()
    order_query: Query = base_store._get_query(table=Order)

    # WHEN filtering orders by a non-existent ticket
    filtered_orders: Query = filter_orders_by_ticket_id(orders=order_query, ticket_id=2)

    # THEN the query should return no order
    assert filtered_orders.count() == 0


def test_filter_orders_by_ticket_id_matching_ticket(base_store: Store, ticket_id: str):
    """Test that the order is returned when filtering by an existing ticket id."""

    order = Order(
        id=1,
        customer_id=1,
        ticket_id=int(ticket_id),
    )
    base_store.session.add(order)
    base_store.session.commit()

    # GIVEN a store containing an order with a matching ticket id
    order_query: Query = base_store._get_query(table=Order)

    # WHEN filtering orders by an existing ticket id
    filtered_orders: Query = filter_orders_by_ticket_id(
        orders=order_query, ticket_id=int(ticket_id)
    )

    # THEN the query should return cases with the matching ticket
    assert filtered_orders.count() == 1
    assert filtered_orders.first().ticket_id == int(ticket_id)
