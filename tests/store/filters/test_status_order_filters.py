from sqlalchemy.orm import Query

from cg.store.filters.status_order_filters import filter_orders_by_ticket_id
from cg.store.models import Order
from cg.store.store import Store


def test_filter_orders_by_ticket_no_matching_ticket(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    """Test that no cases are returned when filtering by a non-existent ticket."""
    # GIVEN a store containing cases with no matching ticket id
    order_query: Query = store_with_multiple_cases_and_samples._get_query(table=Order)

    # WHEN filtering orders by a non-existent ticket
    filtered_orders: Query = filter_orders_by_ticket_id(orders=order_query, ticket_id=000)

    # THEN the query should return no order
    assert filtered_orders.count() == 0


def test_filter_orders_by_ticket_id_matching_ticket(
    store_with_multiple_cases_and_samples: Store, ticket_id: str
):
    """Test that the order is returned when filtering by an existing ticket id."""

    # GIVEN a store containing an order with a matching ticket id
    order_query: Query = store_with_multiple_cases_and_samples._get_query(table=Order)

    # WHEN filtering orders by an existing ticket id
    filtered_cases: Query = filter_orders_by_ticket_id(orders=order_query, ticket=ticket_id)

    # THEN the query should return cases with the matching ticket
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert ticket_id in case.tickets
