from enum import Enum
from sqlalchemy import desc
from sqlalchemy.orm import Query
from sqlalchemy.types import DateTime
from typing import List, Callable

from cg.store.models import Application, ApplicationVersion


def filter_application_versions_by_application(
    application_versions: Query, application: Application, **kwargs
) -> Query:
    """Return the application versions given an application."""
    return application_versions.filter(ApplicationVersion.application == application)


def filter_application_versions_by_application_id(
    application_versions: Query, application_id: int, **kwargs
) -> Query:
    """Return the application versions given an application id."""
    return application_versions.filter(ApplicationVersion.application_id == application_id)


def filter_application_versions_by_version(
    application_versions: Query, version: int, **kwargs
) -> Query:
    """Return the application versions given a version."""
    return application_versions.filter(ApplicationVersion.version == version)


def filter_application_versions_before_date(
    application_versions: Query, date: DateTime, **kwargs
) -> Query:
    """Return the application versions with valid_from before a given date."""
    return application_versions.filter(ApplicationVersion.valid_from < date)


def order_application_versions_by_desc_date(application_versions: Query, **kwargs) -> Query:
    """Returned the application versions ordered by valid_from in descending order."""
    return application_versions.order_by(desc(ApplicationVersion.valid_from))


def apply_application_versions_filter(
    filter_functions: List[Callable],
    application_versions: Query,
    application_id: int = None,
    application: Application = None,
    version: int = None,
    date: DateTime = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    for filter_function in filter_functions:
        application_versions: Query = filter_function(
            application_versions=application_versions,
            application_id=application_id,
            application=application,
            version=version,
            date=date,
        )
    return application_versions


class ApplicationVersionFilter(Enum):
    """Define Application Version filter functions."""

    FILTER_BY_APPLICATION = filter_application_versions_by_application
    FILTER_BY_APPLICATION_ID = filter_application_versions_by_application_id
    FILTER_BY_DATE = filter_application_versions_before_date
    FILTER_BY_VERSION = filter_application_versions_by_version
    ORDER_BY_VALID_FROM = order_application_versions_by_desc_date
