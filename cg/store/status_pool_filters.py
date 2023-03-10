from enum import Enum
from typing import List, Optional, Callable
from alchy import Query
from cg.store.models import Pool


def filter_pools_by_entry_id(pools: Query, entry_id: int, **kwargs) -> Query:
    """Return pools by entry id."""
    return pools.filter(Pool.id == entry_id)


def filter_pools_by_name(pools: Query, name: str, **kwargs) -> Query:
    """Return pools by name."""
    return pools.filter(Pool.name == name)


def filter_pools_is_received(pools: Query, **kwargs) -> Query:
    """Return received pools."""
    return pools.filter(Pool.received_at.isnot(None))


def filter_pools_is_not_received(pools: Query, **kwargs) -> Query:
    """Return not received pools."""
    return pools.filter(Pool.received_at.is_(None))


def filter_pools_is_delivered(pools: Query, **kwargs) -> Query:
    """Return delivered pools."""
    return pools.filter(Pool.delivered_at.isnot(None))


def filter_pools_is_not_delivered(pools: Query, **kwargs) -> Query:
    """Return not delivered pools."""
    return pools.filter(Pool.delivered_at.is_(None))


def filter_pools_by_invoice_id(pools: Query, invoice_id: int, **kwargs):
    """Return a pool by an invoice id."""
    return pools.filter(Pool.invoice_id == invoice_id)


def filter_pools_without_invoice_id(pools: Query, **kwargs) -> Query:
    """Return pools without an invoice id."""
    return pools.filter(Pool.invoice_id.is_(None))


def filter_pools_do_invoice(pools: Query, **kwargs) -> Query:
    """Return pools marked for invoicing."""
    return pools.filter(Pool.no_invoice.is_(False))


def filter_pools_do_not_invoice(pools: Query, **kwargs) -> Query:
    """Return pools marked to skip invoicing."""
    return pools.filter(Pool.no_invoice.is_(True))


def apply_pool_filter(
    functions: List[Callable],
    pools: Query,
    invoice_id: Optional[int] = None,
    entry_id: Optional[int] = None,
    name: Optional[str] = None,
) -> Query:
    """Apply filtering functions to the pool queries and return filtered results"""

    for function in functions:
        pools: Query = function(pools=pools, invoice_id=invoice_id, entry_id=entry_id, name=name)
    return pools


class PoolFilter(Enum):
    """Define Pool filter functions."""

    FILTER_BY_ENTRY_ID: Callable = filter_pools_by_entry_id
    FILTER_BY_NAME: Callable = filter_pools_by_name
    FILTER_IS_RECEIVED: Callable = filter_pools_is_received
    FILTER_IS_NOT_RECEIVED: Callable = filter_pools_is_not_received
    FILTER_IS_DELIVERED: Callable = filter_pools_is_delivered
    FILTER_IS_NOT_DELIVERED: Callable = filter_pools_is_not_delivered
    FILTER_BY_INVOICE_ID: Callable = filter_pools_by_invoice_id
    FILTER_WITHOUT_INVOICE_ID: Callable = filter_pools_without_invoice_id
    FILTER_DO_INVOICE: Callable = filter_pools_do_invoice
    FILTER_DO_NOT_INVOICE: Callable = filter_pools_do_not_invoice
