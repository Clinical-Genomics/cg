from enum import Enum
from typing import List, Optional
from alchy import Query
from cg.store.models import Pool


class PoolFilters(str, Enum):
    get_pool_by_id = ("get_pool_by_id",)
    get_pool_by_name = ("get_pool_by_name",)
    get_pool_is_received = ("get_pool_is_received",)
    get_pool_is_not_received = ("get_pool_is_not_received",)
    get_pool_is_delivered = ("get_pool_is_delivered",)
    get_pool_is_not_delivered = ("get_pool_is_not_delivered",)
    get_pool_without_invoice_id = ("get_pool_without_invoice_id",)
    get_pool_do_invoice = ("get_pool_do_invoice",)
    get_pool_do_not_invoice = ("get_pool_do_not_invoice",)
    get_pool_by_invoice_id = ("get_pool_by_invoice_id",)


def get_pool_by_id(pools: Query, pool_id: int) -> Query:
    """Get a pool by id."""
    return pools.filter(Pool.id == pool_id)


def get_pool_by_name(pools: Query, pool_name: str) -> Query:
    """Get a pool by name."""
    return pools.filter(Pool.name == pool_name)


def get_pool_is_received(pools: Query) -> Query:
    """Get pools that are received."""
    return pools.filter(Pool.received_at.isnot(None))


def get_pool_is_not_received(pools: Query) -> Query:
    """Get pools that are not received."""
    return pools.filter(Pool.received_at.is_(None))


def get_pool_is_delivered(pools: Query) -> Query:
    """Get pools that are delivered."""
    return pools.filter(Pool.delivered_at.isnot(None))


def get_pool_is_not_delivered(pools: Query) -> Query:
    """Get pools that are not delivered."""
    return pools.filter(Pool.delivered_at.is_(None))


def get_pool_by_invoice_id(pools: Query, invoice_id: int):
    """Get a pool by an invoice id."""
    return pools.filter(Pool.invoice_id == invoice_id)


def get_pool_without_invoice_id(pools: Query) -> Query:
    """Get pools that without and invoice_id."""
    return pools.filter(Pool.invoice_id.is_(None))


def get_pool_do_invoice(pools: Query) -> Query:
    """Get pools marked to be invoiced."""
    return pools.filter(Pool.no_invoice.is_(False))


def get_pool_do_not_invoice(pools: Query) -> Query:
    """Get pools marked to skip invoicing."""
    return pools.filter(Pool.no_invoice.is_(True))


def apply_pool_filter(
    functions: List[str], pools: Query, invoice_id: Optional[int] = None
) -> Query:
    """Apply filtering functions to the pool queries and return filtered results"""

    filter_map = {
        PoolFilters.get_pool_by_id: get_pool_by_id,
        PoolFilters.get_pool_by_name: get_pool_by_name,
        PoolFilters.get_pool_is_received: get_pool_is_received,
        PoolFilters.get_pool_is_not_received: get_pool_is_not_received,
        PoolFilters.get_pool_is_delivered: get_pool_is_delivered,
        PoolFilters.get_pool_is_not_delivered: get_pool_is_not_delivered,
        PoolFilters.get_pool_without_invoice_id: get_pool_without_invoice_id,
        PoolFilters.get_pool_do_invoice: get_pool_do_invoice,
        PoolFilters.get_pool_do_not_invoice: get_pool_do_not_invoice,
        PoolFilters.get_pool_by_invoice_id: get_pool_by_invoice_id,
    }

    for function in functions:
        pools: Query = filter_map[function](pools=pools, invoice_id=invoice_id)
    return pools
