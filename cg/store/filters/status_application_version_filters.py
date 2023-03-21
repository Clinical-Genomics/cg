from enum import Enum
from sqlalchemy.orm import Query
from typing import List, Callable

from cg.store.models import Application, ApplicationVersion


def filter_application_version_by_application(
    application_versions: Query, application: Application
) -> Query:
    """Return the application versions of a given application."""
    return application_versions.filter(ApplicationVersion.application == application)


def filter_application_version_by_application_id(
    application_versions: Query, application_id: int
) -> Query:
    """Return the application versions of a given application id."""
    return application_versions.filter(ApplicationVersion.application_id == application_id)


def filter_application_version_by_version(application_versions: Query, version: int) -> Query:
    """Return the application versions of a given version."""
    return application_versions.filter(ApplicationVersion.version == version)


def apply_application_version_filter(
    filter_functions: List[Callable],
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    pass


class ApplicationVersionFilter(Enum):
    """Define Application Version filter functions."""

    pass
