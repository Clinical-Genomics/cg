from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Order


def filter_orders_by_workflow(orders: Query, workflow: str | None, **kwargs) -> Query:
    return orders.filter(Order.workflow == workflow) if workflow else orders


def filter_orders_by_id(orders: Query, id: int | None, **kwargs) -> Query:
    return orders.filter(Order.id == id) if id else orders


def filter_orders_by_ids(orders: Query, ids: list[int] | None, **kwargs) -> Query:
    return orders.filter(Order.id.in_(ids)) if ids else orders


def filter_orders_by_ticket_id(orders: Query, ticket_id: int | None, **kwargs) -> Query:
    return orders.filter(Order.ticket_id == ticket_id) if ticket_id else orders


def apply_limit(orders: Query, limit: int | None, **kwargs) -> Query:
    return orders.limit(limit) if limit else orders


class OrderFilter(Enum):
    BY_ID: Callable = filter_orders_by_id
    BY_IDS: Callable = filter_orders_by_ids
    BY_TICKET_ID: Callable = filter_orders_by_ticket_id
    BY_WORKFLOW: Callable = filter_orders_by_workflow
    APPLY_LIMIT: Callable = apply_limit


def apply_order_filters(
    filters: list[OrderFilter],
    orders: Query,
    id: int = None,
    ids: list[int] = None,
    ticket_id: int = None,
    workflow: str = None,
    limit: int = None,
) -> Query:
    for filter in filters:
        orders: Query = filter(
            orders=orders, id=id, ids=ids, ticket_id=ticket_id, workflow=workflow, limit=limit
        )
    return orders
