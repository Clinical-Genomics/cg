from enum import Enum
from typing import List, Optional, Callable
from alchy import Query
from cg.store.models import Pool


def filter_pools_by_id(pools: Query, pool_id: int) -> Query:
    """Get a pool by id."""
    return pools.filter(Pool.id == pool_id)


def filter_pools_by_name(pools: Query, pool_name: str) -> Query:
    """Get a pool by name."""
    return pools.filter(Pool.name == pool_name)


def filter_pools_is_received(pools: Query) -> Query:
    """Get pools that are received."""
    return pools.filter(Pool.received_at.isnot(None))


def filter_pools_is_not_received(pools: Query) -> Query:
    """Get pools that are not received."""
    return pools.filter(Pool.received_at.is_(None))


def filter_pools_is_delivered(pools: Query) -> Query:
    """Get pools that are delivered."""
    return pools.filter(Pool.delivered_at.isnot(None))


def filter_pools_is_not_delivered(pools: Query) -> Query:
    """Get pools that are not delivered."""
    return pools.filter(Pool.delivered_at.is_(None))


def filter_pools_by_invoice_id(pools: Query, invoice_id: int):
    """Get a pool by an invoice id."""
    return pools.filter(Pool.invoice_id == invoice_id)


def filter_pools_without_invoice_id(pools: Query) -> Query:
    """Get pools that without and invoice_id."""
    return pools.filter(Pool.invoice_id.is_(None))


def filter_pools_do_invoice(pools: Query) -> Query:
    """Get pools marked to be invoiced."""
    return pools.filter(Pool.no_invoice.is_(False))


def filter_pools_do_not_invoice(pools: Query) -> Query:
    """Get pools marked to skip invoicing."""
    return pools.filter(Pool.no_invoice.is_(True))


def apply_pool_filter(
    functions: List[Callable], pools: Query, invoice_id: Optional[int] = None
) -> Query:
    """Apply filtering functions to the pool queries and return filtered results"""

    for function in functions:
        pools: Query = function(pools=pools, invoice_id=invoice_id)
    return pools


class PoolFilters(Enum):
    filter_pools_by_id: Callable = filter_pools_by_id
    filter_pools_by_name: Callable = filter_pools_by_name
    filter_pools_is_received: Callable = filter_pools_is_received
    filter_pools_is_not_received: Callable = filter_pools_is_not_received
    filter_pools_is_delivered: Callable = filter_pools_is_delivered
    filter_pools_is_not_delivered: Callable = filter_pools_is_not_delivered
    filter_pools_by_invoice_id: Callable = filter_pools_by_invoice_id
    filter_pools_without_invoice_id: Callable = filter_pools_without_invoice_id
    filter_pools_do_invoice: Callable = filter_pools_do_invoice
    filter_pools_do_not_invoice: Callable = filter_pools_do_not_invoice
