from typing import List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.store.models import Application


def get_applications_by_tag(applications: Query, tag: str, **kwargs) -> Query:
    """Return application by tag."""
    return applications.filter(Application.tag == tag)


def get_applications_by_prep_category(applications: Query, prep_category: str, **kwargs) -> Query:
    """Return application by prep category."""
    return applications.filter(Application.prep_category == prep_category)


def get_applications_is_archived(applications: Query, **kwargs) -> Query:
    """Return application with archived."""
    return applications.filter(Application.is_archived.is_(True))


def get_applications_by_id(applications: Query, application_id: int, **kwargs) -> Query:
    """Return application by id."""
    return applications.filter(Application.id == application_id)


def get_applications_is_external(applications: Query, **kwargs) -> Query:
    """Return application with external."""
    return applications.filter(Application.is_external == True)


def get_applications_is_not_external(applications: Query, **kwargs) -> Query:
    """Return application with external."""
    return applications.filter(Application.is_external == False)


def apply_application_filter(
    functions: List[Callable],
    applications: Query,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for function in functions:
        applications: Query = function(
            applications=applications,
        )
    return applications


class ApplicationFilters(Enum):
    """Enum with filtering functions for applications."""

    get_applications_is_external = get_applications_is_external
    get_applications_is_not_external = get_applications_is_not_external
    get_applications_by_tag = get_applications_by_tag
    get_applications_by_prep_category = get_applications_by_prep_category
    get_applications_is_archived = get_applications_is_archived
    get_applications_by_id = get_applications_by_id
