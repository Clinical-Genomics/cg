from typing import List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.constants import REPORT_SUPPORTED_PIPELINES
from cg.constants.constants import VALID_DATA_IN_PRODUCTION
from cg.store.models import Analysis
from cgmodels.cg.constants import Pipeline


def get_valid_analyses_in_production(analyses: Query, **kwargs) -> Query:
    """Return analyses with a valid data in production."""
    return analyses.filter(VALID_DATA_IN_PRODUCTION < Analysis.completed_at)


def get_analyses_with_pipeline(analyses: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Return analyses with supplied pipeline."""
    return analyses.filter(Analysis.pipeline == str(pipeline)) if pipeline else analyses


def get_completed_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have been completed."""
    return analyses.filter(Analysis.completed_at.isnot(None))


def get_not_completed_analyses(analyses: Query, **kwargs) -> Query:
    """Return not completed analyses."""
    return analyses.filter(Analysis.completed_at.is_(None))


def get_filter_uploaded_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have been already uploaded."""
    return analyses.filter(Analysis.uploaded_at.isnot(None))


def get_not_uploaded_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have not been uploaded."""
    return analyses.filter(Analysis.uploaded_at.is_(None))


def get_analyses_with_delivery_report(analyses: Query, **kwargs) -> Query:
    """Return analyses that have a delivery report generated."""
    return analyses.filter(Analysis.delivery_report_created_at.isnot(None))


def get_analyses_without_delivery_report(analyses: Query, **kwargs) -> Query:
    """Return analyses that do not have a delivery report generated."""
    return analyses.filter(Analysis.delivery_report_created_at.is_(None))


def get_report_analyses_by_pipeline(analyses: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Return the delivery report related analyses associated to the provided or supported pipelines."""
    return (
        analyses.filter(Analysis.pipeline == str(pipeline))
        if pipeline
        else analyses.filter(Analysis.pipeline.in_(REPORT_SUPPORTED_PIPELINES))
    )


def order_analyses_by_completed_at(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the completed_at field."""
    return analyses.order_by(Analysis.completed_at.asc())


def order_analyses_by_uploaded_at(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the uploaded_at field."""
    return analyses.order_by(Analysis.uploaded_at.asc())


def apply_analysis_filter(
    filter_functions: List[Callable], analyses: Query, pipeline: Pipeline = None
) -> Query:
    """Apply filtering functions to the analyses queries and return filtered results."""

    for function in filter_functions:
        analyses: Query = function(
            analyses=analyses,
            pipeline=pipeline,
        )
    return analyses


class AnalysisFilter(Enum):
    """Define Analysis filter functions."""

    FILTER_VALID_IN_PRODUCTION: Callable = get_valid_analyses_in_production
    FILTER_WITH_PIPELINE: Callable = get_analyses_with_pipeline
    FILTER_COMPLETED: Callable = get_completed_analyses
    FILTER_NOT_COMPLETED: Callable = get_not_completed_analyses
    FILTER_UPLOADED: Callable = get_filter_uploaded_analyses
    FILTER_NOT_UPLOADED: Callable = get_not_uploaded_analyses
    FILTER_WITH_DELIVERY_REPORT: Callable = get_analyses_with_delivery_report
    FILTER_WITHOUT_DELIVERY_REPORT: Callable = get_analyses_without_delivery_report
    FILTER_REPORT_BY_PIPELINE: Callable = get_report_analyses_by_pipeline
    ORDER_BY_COMPLETED_AT: Callable = order_analyses_by_completed_at
