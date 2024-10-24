from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.constants import PrepCategory, Workflow
from cg.store.models import Application


def filter_applications_by_tag(applications: Query, tag: str, **kwargs) -> Query:
    """Return application by tag."""
    return applications.filter(Application.tag == tag)


def filter_applications_is_not_archived(applications: Query, **kwargs) -> Query:
    """Return application which is not archived."""
    return applications.filter(Application.is_archived.is_(False))


def filter_applications_is_external(applications: Query, **kwargs) -> Query:
    """Return application which is external."""
    return applications.filter(Application.is_external == True)


def filter_applications_is_not_external(applications: Query, **kwargs) -> Query:
    """Return application which is not external."""
    return applications.filter(Application.is_external == False)


def filter_applications_has_versions(applications: Query, **kwargs) -> Query:
    return applications.filter(Application.versions.any())


def filter_application_by_prep_categories(
    applications: Query, prep_categories: list[PrepCategory], **kwargs
) -> Query:
    """Return application corresponding to dna sequencing."""
    return applications.filter(Application.prep_category.in_(prep_categories))


def apply_application_filter(
    filter_functions: list[Callable],
    applications: Query,
    tag: str = None,
    prep_category: str = None,
    prep_categories: list[Workflow] = None,
    entry_id: int = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for filter_function in filter_functions:
        applications: Query = filter_function(
            applications=applications,
            tag=tag,
            prep_category=prep_category,
            prep_categories=prep_categories,
            entry_id=entry_id,
        )
    return applications


class ApplicationFilter(Enum):
    """Define Application filter functions."""

    HAS_VERSIONS = filter_applications_has_versions
    IS_EXTERNAL = filter_applications_is_external
    IS_NOT_EXTERNAL = filter_applications_is_not_external
    BY_TAG = filter_applications_by_tag
    IS_NOT_ARCHIVED = filter_applications_is_not_archived
    BY_PREP_CATEGORIES = filter_application_by_prep_categories
