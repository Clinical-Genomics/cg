from enum import Enum
from typing import Callable

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Query

from cg.constants import Workflow
from cg.server.dto.orders.orders_request import OrderSortField, SortOrder
from cg.store.models import Customer, Order


def filter_orders_by_id(orders: Query, id: int | None, **kwargs) -> Query:
    return orders.filter(Order.id == id) if id else orders


def filter_orders_by_ids(orders: Query, ids: list[int] | None, **kwargs) -> Query:
    return orders.filter(Order.id.in_(ids))


def apply_pagination(orders: Query, page: int | None, page_size: int | None, **kwargs) -> Query:
    return orders.limit(page_size).offset((page - 1) * page_size) if page and page_size else orders


def filter_orders_by_ticket_id(orders: Query, ticket_id: int | None, **kwargs) -> Query:
    return orders.filter(Order.ticket_id == ticket_id) if ticket_id else orders


def filter_orders_by_search(orders: Query, search: str | None, **kwargs) -> Query:
    if not search:
        return orders

    orders = orders.join(Order.customer)
    return orders.filter(
        or_(
            Order.id == search,
            Order.ticket_id == search,
            Customer.internal_id.icontains(search),
        )
    )


def filter_orders_by_is_open(orders: Query, is_open: bool | None, **kwargs) -> Query:
    return orders.filter(Order.is_open == is_open) if is_open is not None else orders


def apply_sorting(
    orders: Query, sort_field: OrderSortField | None, sort_order: SortOrder | None, **kwargs
) -> Query:
    if sort_field:
        column = getattr(Order, sort_field)
        if sort_order == "asc":
            return orders.order_by(asc(column))
        return orders.order_by(desc(column))
    return orders


class OrderFilter(Enum):
    BY_ID: Callable = filter_orders_by_id
    BY_IDS: Callable = filter_orders_by_ids
    BY_SEARCH: Callable = filter_orders_by_search
    BY_TICKET_ID: Callable = filter_orders_by_ticket_id
    BY_OPEN: Callable = filter_orders_by_is_open
    PAGINATE: Callable = apply_pagination
    SORT: Callable = apply_sorting


def apply_order_filters(
    filters: list[OrderFilter],
    orders: Query,
    id: int = None,
    ids: list[int] = None,
    ticket_id: int = None,
    page: int = None,
    page_size: int = None,
    sort_field: OrderSortField = None,
    sort_order: SortOrder = None,
    search: str = None,
    is_open: bool = None,
) -> Query:
    for filter in filters:
        orders: Query = filter(
            orders=orders,
            id=id,
            ids=ids,
            page=page,
            page_size=page_size,
            ticket_id=ticket_id,
            sort_field=sort_field,
            sort_order=sort_order,
            search=search,
            is_open=is_open,
        )
    return orders
