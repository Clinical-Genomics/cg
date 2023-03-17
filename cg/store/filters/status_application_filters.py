from typing import List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.store.models import Application


def filter_applications_by_tag(applications: Query, tag: str, **kwargs) -> Query:
    """Return application by tag."""
    return applications.filter(Application.tag == tag)


def filter_applications_by_prep_category(
    applications: Query, prep_category: str, **kwargs
) -> Query:
    """Return application by prep category."""
    return applications.filter(Application.prep_category == prep_category)


def filter_applications_is_archived(applications: Query, **kwargs) -> Query:
    """Return application which is archived."""
    return applications.filter(Application.is_archived.is_(True))


def filter_applications_is_not_archived(applications: Query, **kwargs) -> Query:
    """Return application which is not archived."""
    return applications.filter(Application.is_archived.is_(False))


def filter_applications_by_entry_id(applications: Query, entry_id: int, **kwargs) -> Query:
    """Return application by entry id."""
    return applications.filter(Application.id == entry_id)


def filter_applications_is_external(applications: Query, **kwargs) -> Query:
    """Return application which is external."""
    return applications.filter(Application.is_external == True)


def filter_applications_is_not_external(applications: Query, **kwargs) -> Query:
    """Return application which is not external."""
    return applications.filter(Application.is_external == False)


def apply_application_filter(
    filter_functions: List[Callable],
    applications: Query,
    tag: str = None,
    prep_category: str = None,
    entry_id: int = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for filter_function in filter_functions:
        applications: Query = filter_function(
            applications=applications,
            tag=tag,
            prep_category=prep_category,
            entry_id=entry_id,
        )
    return applications


class ApplicationFilter(Enum):
    """Define Application filter functions."""

    FILTER_IS_EXTERNAL = filter_applications_is_external
    FILTER_IS_NOT_EXTERNAL = filter_applications_is_not_external
    FILTER_BY_TAG = filter_applications_by_tag
    FILTER_BY_PREP_CATEGORY = filter_applications_by_prep_category
    FILTER_IS_ARCHIVED = filter_applications_is_archived
    FILTER_IS_NOT_ARCHIVED = filter_applications_is_not_archived
    FILTER_BY_ID = filter_applications_by_entry_id
