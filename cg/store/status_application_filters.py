from typing import List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.store.models import Application


def filter_applications_by_tag(applications: Query, tag: str, **kwargs) -> Query:
    """Filter application by tag."""
    return applications.filter(Application.tag == tag)


def filter_applications_by_prep_category(
    applications: Query, prep_category: str, **kwargs
) -> Query:
    """Filter application by prep category."""
    return applications.filter(Application.prep_category == prep_category)


def filter_applications_is_archived(applications: Query, **kwargs) -> Query:
    """Filter application with archived."""
    return applications.filter(Application.is_archived.is_(True))


def filter_applications_by_entry_id(applications: Query, entry_id: int, **kwargs) -> Query:
    """Filter application by id."""
    return applications.filter(Application.id == entry_id)


def filter_applications_is_external(applications: Query, **kwargs) -> Query:
    """Filter application with external."""
    return applications.filter(Application.is_external == True)


def filter_applications_is_not_external(applications: Query, **kwargs) -> Query:
    """Filter application with external."""
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

    FILTER_IS_EXTERNAL = filter_applications_is_external
    FILTER_IS_NOT_EXTERNAL = filter_applications_is_not_external
    FILTER_BY_TAG = filter_applications_by_tag
    FILTER_BY_PREP_CATEGORY = filter_applications_by_prep_category
    FILTER_IS_ARCHIVED = filter_applications_is_archived
    FILTER_BY_ID = filter_applications_by_entry_id
