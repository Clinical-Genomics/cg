from enum import Enum
from sqlalchemy.orm import Query
from typing import List, Callable

from cg.store.models import Application, ApplicationVersion


def filter_application_version_by_application(
    application_versions: Query, application: Application
) -> Query:
    """Return the application versions given an application."""
    return application_versions.filter(ApplicationVersion.application == application)


def filter_application_version_by_application_id(
    application_versions: Query, application_id: int
) -> Query:
    """Return the application versions given an application id."""
    return application_versions.filter(ApplicationVersion.application_id == application_id)


def filter_application_version_by_version(application_versions: Query, version: int) -> Query:
    """Return the application versions given a version."""
    return application_versions.filter(ApplicationVersion.version == version)


def apply_application_version_filter(
    filter_functions: List[Callable],
    application_versions: Query,
    application_id: int = None,
    application: Application = None,
    version: int = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    for filter_function in filter_functions:
        application_versions: Query = filter_function(
            application_versions=application_versions,
            application_id=application_id,
            applicatiomn=application,
            version=version,
        )
    return application_versions


class ApplicationVersionFilter(Enum):
    """Define Application Version filter functions."""

    FILTER_BY_APPLICATION = filter_application_version_by_application
    FILTER_BY_APPLICATION_ID = filter_application_version_by_application_id
    FILTER_BY_VERSION = filter_application_version_by_version
