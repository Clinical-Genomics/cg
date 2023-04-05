from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Query
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


def filter_application_versions_before_valid_from(
    application_versions: Query, valid_from: datetime, **kwargs
) -> Query:
    """Return the application versions with valid_from before a given valid_from date."""
    return application_versions.filter(ApplicationVersion.valid_from < valid_from)


def order_application_versions_by_valid_from_desc(application_versions: Query, **kwargs) -> Query:
    """Returned the application versions ordered by valid_from in descending order."""
    return application_versions.order_by(ApplicationVersion.valid_from.desc())


def apply_application_versions_filter(
    filter_functions: List[Callable],
    application_versions: Query,
    application_id: int = None,
    application: Application = None,
    version: int = None,
    valid_from: datetime = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    for filter_function in filter_functions:
        application_versions: Query = filter_function(
            application_versions=application_versions,
            application_id=application_id,
            application=application,
            version=version,
            valid_from=valid_from,
        )
    return application_versions


class ApplicationVersionFilter(Enum):
    """Define Application Version filter functions."""

    FILTER_BY_APPLICATION = filter_application_versions_by_application
    FILTER_BY_APPLICATION_ID = filter_application_versions_by_application_id
    FILTER_BY_VALID_FROM_BEFORE = filter_application_versions_before_valid_from
    FILTER_BY_VERSION = filter_application_versions_by_version
    ORDER_BY_VALID_FROM_DESC = order_application_versions_by_valid_from_desc
