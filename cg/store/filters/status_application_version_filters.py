from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Query
from typing import List, Callable

from cg.store.models import ApplicationVersion


def filter_application_versions_by_application_entry_id(
    application_versions: Query, application_entry_id: int, **kwargs
) -> Query:
    """Return the application versions given an application entry id."""
    return application_versions.filter(ApplicationVersion.application_id == application_entry_id)


def filter_application_versions_before_valid_from(
    application_versions: Query, valid_from: datetime, **kwargs
) -> Query:
    """Return the application versions with valid_from before a given valid_from date."""
    return application_versions.filter(ApplicationVersion.valid_from < valid_from)


def order_application_versions_by_valid_from_desc(application_versions: Query, **kwargs) -> Query:
    """Returned the application versions ordered by valid_from in descending order."""
    return application_versions.order_by(ApplicationVersion.valid_from.desc())


def filter_application_versions_by_application_version_entry_id(
    application_versions: Query,
    application_version_entry_id,
    **kwargs,
) -> Query:
    """Return the application versions given an application version entry id."""
    return application_versions.filter(ApplicationVersion.id == application_version_entry_id)


def apply_application_versions_filter(
    filter_functions: List[Callable],
    application_versions: Query,
    application_entry_id: int = None,
    application_version_entry_id: int = None,
    version: int = None,
    valid_from: datetime = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    for filter_function in filter_functions:
        application_versions: Query = filter_function(
            application_versions=application_versions,
            application_entry_id=application_entry_id,
            application_version_entry_id=application_version_entry_id,
            version=version,
            valid_from=valid_from,
        )
    return application_versions


class ApplicationVersionFilter(Enum):
    """Define Application Version filter functions."""

    FILTER_BY_APPLICATION_ENTRY_ID = filter_application_versions_by_application_entry_id
    FILTER_BY_ENTRY_ID = filter_application_versions_by_application_version_entry_id
    FILTER_BY_VALID_FROM_BEFORE = filter_application_versions_before_valid_from
    ORDER_BY_VALID_FROM_DESC = order_application_versions_by_valid_from_desc
