from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.constants import Workflow
from cg.store.models import Application, ApplicationLimitations


def filter_application_limitations_by_tag(
    application_limitations: Query, tag: str, **kwargs
) -> Query:
    """Return application limitations by tag."""
    return application_limitations.filter(Application.tag == tag)


def filter_application_limitations_by_workflow(
    application_limitations: Query, workflow: Workflow, **kwargs
) -> Query:
    """Return application limitations by workflow."""
    return application_limitations.filter(ApplicationLimitations.workflow == workflow)


def apply_application_limitations_filter(
    filter_functions: list[Callable],
    application_limitations: Query,
    tag: str = None,
    workflow: Workflow = None,
) -> Query:
    """Apply filtering functions to the application limitations queries and return filtered results."""
    for filter_function in filter_functions:
        application_limitations: Query = filter_function(
            application_limitations=application_limitations,
            tag=tag,
            workflow=workflow,
        )
    return application_limitations


class ApplicationLimitationsFilter(Enum):
    """Define ApplicationLimitations filter functions."""

    BY_TAG = filter_application_limitations_by_tag
    BY_WORKFLOW = filter_application_limitations_by_workflow
