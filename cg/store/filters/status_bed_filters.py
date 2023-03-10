from enum import Enum
from typing import List, Optional, Callable

from sqlalchemy.orm import Query

from cg.store.models import Bed


def get_beds_by_name(beds: Query, bed_name: str, **kwargs) -> Query:
    """Return beds by name."""
    return beds.filter(Bed.name == bed_name)


def get_not_archived_beds(beds: Query, **kwargs) -> Query:
    """Return beds not archived."""
    return beds.filter(Bed.is_archived.is_(False))


def order_beds_by_name(beds: Query, **kwargs) -> Query:
    """Return beds ordered by name."""
    return beds.order_by(Bed.name)


class BedFilters(Enum):
    """Define BED filter functions."""

    get_beds_by_name: Callable = get_beds_by_name
    get_not_archived_beds: Callable = get_not_archived_beds
    order_beds_by_name: Callable = order_beds_by_name


def apply_bed_filter(
    beds: Query,
    functions: List[Callable],
    bed_name: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in functions:
        beds: Query = function(
            beds=beds,
            bed_name=bed_name,
        )
    return beds
