from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Order


def filter_orders_by_workflow(orders: Query, workflow: str | None, **kwargs) -> Query:
    return orders.filter(Order.workflow == workflow) if workflow else orders


def filter_orders_by_id(orders: Query, id: int | None, **kwargs) -> Query:
    return orders.filter(Order.id == id) if id else orders


def filter_by_limit(orders: Query, limit: int | None, **kwargs) -> Query:
    return orders.limit(limit) if limit else orders


def apply_order_filters(
    filters: list[Callable], orders: Query, id: int = None, workflow: str = None, limit: int = None
) -> Query:
    for filter in filters:
        orders: Query = filter(orders=orders, id=id, workflow=workflow, limit=limit)
    return orders


class OrderFilter(Enum):
    """Define order filter functions."""

    BY_ID: Callable = filter_orders_by_id
    BY_WORKFLOW: Callable = filter_orders_by_workflow
    APPLY_LIMIT: Callable = filter_by_limit
