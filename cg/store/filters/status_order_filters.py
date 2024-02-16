from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Order


def get_orders_by_workflow(orders: Query, workflow: str, **kwargs) -> Query:
    """Return orders filtered on workflow."""
    return orders.filter(Order.workflow == workflow) if workflow else orders


def get_orders_by_id(orders: Query, id: int, **kwargs) -> Query:
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

    GET_ORDERS_BY_ID: Callable = get_orders_by_id
    GET_ORDERS_BY_WORKFLOW: Callable = get_orders_by_workflow
