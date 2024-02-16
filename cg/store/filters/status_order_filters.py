from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Order


def filter_orders_by_workflow(orders: Query, workflow: str, **kwargs) -> Query:
    """Return orders filtered on workflow."""
    return orders.filter(Order.workflow == workflow) if workflow else orders


def filter_orders_by_id(orders: Query, id: int, **kwargs) -> Query:
    """Return orders filtered on id."""
    return orders.filter(Order.id == id)


def apply_order_filters(
    filter_functions: list[Callable], orders: Query, id: int = None, workflow: str = None
) -> Query:
    """Apply filtering functions to the order queries and return filtered results."""
    for filter_function in filter_functions:
        orders: Query = filter_function(orders=orders, id=id, workflow=workflow)
    return orders


class OrderFilter(Enum):
    """Define order filter functions."""

    FILTER_ORDERS_BY_ID: Callable = filter_orders_by_id
    FILTER_ORDERS_BY_WORKFLOW: Callable = filter_orders_by_workflow
