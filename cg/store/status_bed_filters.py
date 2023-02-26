from typing import List

from sqlalchemy.orm import Query

from cg.store.models import Bed


def get_not_archived_beds(beds: Query, **kwargs) -> Bed:
    """Return beds not archived."""
    return beds.filter(Bed.is_archived.is_(False))


def order_beds_by_name(beds: Query, **kwargs) -> Bed:
    """Return beds ordered by name."""
    return beds.order_by(Bed.name)


def apply_bed_filter(
    beds: Query,
    functions: List[str],
) -> Query:
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "get_not_archived_beds": get_not_archived_beds,
        "order_beds_by_name": order_beds_by_name,
    }
    for function in functions:
        beds: Query = filter_map[function](
            beds=beds,
        )
    return beds
