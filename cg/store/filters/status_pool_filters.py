from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Customer, Pool


def get_pools_by_customer_id(pools: Query, customer_ids: list[int], **kwargs) -> Query:
    """Return pools by customer id."""
    return pools.filter(Pool.customer_id.in_(customer_ids))


def get_pools_by_name_enquiry(pools: Query, name_enquiry: str, **kwargs) -> Query:
    """Return pools by name enquiry."""
    return pools.filter(Pool.name.like(f"%{name_enquiry}%"))


def get_pools_by_order_enquiry(pools: Query, order_enquiry: str, **kwargs) -> Query:
    """Return pools by order enquiry."""
    return pools.filter(Pool.order.like(f"%{order_enquiry}%"))


def get_pools_by_entry_id(pools: Query, entry_id: int, **kwargs) -> Query:
    """Return pools by entry id."""
    return pools.filter(Pool.id == entry_id)


def get_pools_by_name(pools: Query, name: str, **kwargs) -> Query:
    """Return pools by name."""
    return pools.filter(Pool.name == name)


def get_pools_is_received(pools: Query, **kwargs) -> Query:
    """Return received pools."""
    return pools.filter(Pool.received_at.isnot(None))


def get_pools_is_not_received(pools: Query, **kwargs) -> Query:
    """Return not received pools."""
    return pools.filter(Pool.received_at.is_(None))


def get_pools_is_delivered(pools: Query, **kwargs) -> Query:
    """Return delivered pools."""
    return pools.filter(Pool.delivered_at.isnot(None))


def get_pools_is_not_delivered(pools: Query, **kwargs) -> Query:
    """Return not delivered pools."""
    return pools.filter(Pool.delivered_at.is_(None))


def get_pools_by_invoice_id(pools: Query, invoice_id: int, **kwargs):
    """Return a pool by an invoice id."""
    return pools.filter(Pool.invoice_id == invoice_id)


def get_pools_without_invoice_id(pools: Query, **kwargs) -> Query:
    """Return pools without an invoice id."""
    return pools.filter(Pool.invoice_id.is_(None))


def get_pools_do_invoice(pools: Query, **kwargs) -> Query:
    """Return pools marked for invoicing."""
    return pools.filter(Pool.no_invoice.is_(False))


def get_pools_by_customer(pools: Query, customer: Customer, **kwargs) -> Query:
    """Return pools by customer id."""
    return pools.filter(Pool.customer == customer)


def apply_pool_filter(
    filter_functions: list[Callable],
    pools: Query,
    invoice_id: int | None = None,
    entry_id: int | None = None,
    name: str | None = None,
    customer_ids: list[int] | None = None,
    name_enquiry: str | None = None,
    order_enquiry: str | None = None,
    customer: Customer | None = None,
) -> Query:
    """Apply filtering functions to the pool queries and return filtered results"""

    for filter_function in filter_functions:
        pools: Query = filter_function(
            pools=pools,
            invoice_id=invoice_id,
            entry_id=entry_id,
            name=name,
            customer_ids=customer_ids,
            name_enquiry=name_enquiry,
            order_enquiry=order_enquiry,
            customer=customer,
        )
    return pools


class PoolFilter(Enum):
    """Define Pool filter functions."""

    GET_BY_ENTRY_ID: Callable = get_pools_by_entry_id
    GET_BY_NAME: Callable = get_pools_by_name
    GET_IS_RECEIVED: Callable = get_pools_is_received
    GET_IS_NOT_RECEIVED: Callable = get_pools_is_not_received
    GET_IS_DELIVERED: Callable = get_pools_is_delivered
    GET_IS_NOT_DELIVERED: Callable = get_pools_is_not_delivered
    GET_BY_INVOICE_ID: Callable = get_pools_by_invoice_id
    GET_WITHOUT_INVOICE_ID: Callable = get_pools_without_invoice_id
    GET_DO_INVOICE: Callable = get_pools_do_invoice
    GET_BY_CUSTOMER_ID: Callable = get_pools_by_customer_id
    GET_BY_NAME_ENQUIRY: Callable = get_pools_by_name_enquiry
    GET_BY_ORDER_ENQUIRY: Callable = get_pools_by_order_enquiry
    GET_BY_CUSTOMER: Callable = get_pools_by_customer
