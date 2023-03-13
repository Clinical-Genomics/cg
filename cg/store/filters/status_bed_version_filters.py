from enum import Enum
from typing import List, Optional, Callable

from sqlalchemy.orm import Query

from cg.store.models import BedVersion


def get_bed_version_by_short_name(
    bed_versions: Query, bed_version_short_name: str, **kwargs
) -> Query:
    """Return beds by short name."""
    return bed_versions.filter(BedVersion.shortname == bed_version_short_name)


class BedVersionFilter(Enum):
    """Define BED version filter functions."""

    FILTER_BY_SHORT_NAME: Callable = get_bed_version_by_short_name


def apply_bed_version_filter(
    bed_versions: Query,
    filter_functions: List[Callable],
    bed_version_short_name: Optional[str] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        bed_versions: Query = function(
            bed_versions=bed_versions,
            bed_version_short_name=bed_version_short_name,
        )
    return bed_versions
