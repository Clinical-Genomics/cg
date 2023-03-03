from enum import Enum
from typing import List, Optional, Callable

from sqlalchemy.orm import Query

from cg.store.models import BedVersion


def get_bed_version_by_short_name(
    bed_versions: Query, bed_version_short_name: str, **kwargs
) -> Query:
    """Return beds by short name."""
    return bed_versions.filter(BedVersion.shortname == bed_version_short_name)


class BedVersionFilters(Enum):
    """Define BED version filter functions."""

    get_bed_version_by_short_name: Callable = get_bed_version_by_short_name


def apply_bed_version_filter(
    bed_versions: Query,
    functions: List[Callable],
    bed_version_short_name: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in functions:
        bed_versions: Query = function(
            bed_versions=bed_versions,
            bed_version_short_name=bed_version_short_name,
        )
    return bed_versions
