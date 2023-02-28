from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query


from cg.store.models import Application


def get_application_is_external(applications: Query, **kwargs) -> Query:
    """Return application with external."""
    return applications.filter(Application.is_external == True)


def get_application_is_not_external(applications: Query, **kwargs) -> Query:
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

    get_application_is_external = get_application_is_external
    get_application_is_not_external = get_application_is_not_external
