from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import Bed


def filter_bed_by_entry_id(beds: Query, bed_entry_id: int, **kwargs) -> Query:
    """Return bed by foreign key."""
    return beds.filter(Bed.id == bed_entry_id)


def filter_bed_by_name(beds: Query, bed_name: str, **kwargs) -> Query:
    """Return bed by name."""
    return beds.filter(Bed.name == bed_name)


def filter_not_archived_beds(beds: Query, **kwargs) -> Query:
    """Return beds not archived."""
    return beds.filter(Bed.is_archived.is_(False))


def order_beds_by_name(beds: Query, **kwargs) -> Query:
    """Return beds ordered by name."""
    return beds.order_by(Bed.name)


class BedFilter(Enum):
    """Define BED filter functions."""

    BY_ENTRY_ID: Callable = filter_bed_by_entry_id
    BY_NAME: Callable = filter_bed_by_name
    NOT_ARCHIVED: Callable = filter_not_archived_beds
    ORDER_BY_NAME: Callable = order_beds_by_name


def apply_bed_filter(
    beds: Query,
    filter_functions: list[Callable],
    bed_entry_id: int | None = None,
    bed_name: str | None = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        beds: Query = function(
            beds=beds,
            bed_entry_id=bed_entry_id,
            bed_name=bed_name,
        )
    return beds
