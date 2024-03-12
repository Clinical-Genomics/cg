from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.store.models import BedVersion


def filter_bed_version_by_file_name(
    bed_versions: Query, bed_version_file_name: str, **kwargs
) -> Query:
    """Return beds by file name."""
    return bed_versions.filter(BedVersion.filename == bed_version_file_name)


def filter_bed_version_by_short_name(
    bed_versions: Query, bed_version_short_name: str, **kwargs
) -> Query:
    """Return beds by short name."""
    return bed_versions.filter(BedVersion.shortname == bed_version_short_name)


class BedVersionFilter(Enum):
    """Define BED version filter functions."""

    BY_FILE_NAME: Callable = filter_bed_version_by_file_name
    BY_SHORT_NAME: Callable = filter_bed_version_by_short_name


def apply_bed_version_filter(
    bed_versions: Query,
    filter_functions: list[Callable],
    bed_version_file_name: str | None = None,
    bed_version_short_name: str | None = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        bed_versions: Query = function(
            bed_versions=bed_versions,
            bed_version_file_name=bed_version_file_name,
            bed_version_short_name=bed_version_short_name,
        )
    return bed_versions
