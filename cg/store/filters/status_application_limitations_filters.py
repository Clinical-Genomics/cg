from enum import Enum
from typing import Callable

from sqlalchemy.orm import Query

from cg.constants import Pipeline
from cg.store.models import Application, ApplicationLimitations


def filter_application_limitations_by_tag(
    application_limitations: Query, tag: str, **kwargs
) -> Query:
    """Return application limitations by tag."""
    return application_limitations.filter(Application.tag == tag)


def filter_application_limitations_by_pipeline(
    application_limitations: Query, pipeline: Pipeline, **kwargs
) -> Query:
    """Return application limitations by pipeline."""
    return application_limitations.filter(ApplicationLimitations.pipeline == pipeline)


def apply_application_limitations_filter(
    filter_functions: list[Callable],
    application_limitations: Query,
    tag: str = None,
    pipeline: Pipeline = None,
) -> Query:
    """Apply filtering functions to the application limitations queries and return filtered results."""
    for filter_function in filter_functions:
        application_limitations: Query = filter_function(
            application_limitations=application_limitations,
            tag=tag,
            pipeline=pipeline,
        )
    return application_limitations


class ApplicationLimitationsFilter(Enum):
    """Define ApplicationLimitations filter functions."""

    FILTER_BY_TAG = filter_application_limitations_by_tag
    FILTER_BY_PIPELINE = filter_application_limitations_by_pipeline
