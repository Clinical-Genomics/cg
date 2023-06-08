from typing import List, Callable
from enum import Enum
from sqlalchemy.orm import Query


from cg.constants import REPORT_SUPPORTED_PIPELINES
from cg.constants.constants import VALID_DATA_IN_PRODUCTION
from cg.store.models import Analysis, Family
from cgmodels.cg.constants import Pipeline
from datetime import datetime


def filter_valid_analyses_in_production(analyses: Query, **kwargs) -> Query:
    """Return analyses with a valid data in production."""
    return analyses.filter(VALID_DATA_IN_PRODUCTION < Analysis.completed_at)


def filter_analyses_with_pipeline(analyses: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Return analyses with supplied pipeline."""
    return analyses.filter(Analysis.pipeline == str(pipeline)) if pipeline else analyses


def filter_completed_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have been completed."""
    return analyses.filter(Analysis.completed_at.isnot(None))


def filter_uploaded_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have been already uploaded."""
    return analyses.filter(Analysis.uploaded_at.isnot(None))


def filter_not_uploaded_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have not been uploaded."""
    return analyses.filter(Analysis.uploaded_at.is_(None))


def filter_analyses_with_delivery_report(analyses: Query, **kwargs) -> Query:
    """Return analyses that have a delivery report generated."""
    return analyses.filter(Analysis.delivery_report_created_at.isnot(None))


def filter_analyses_without_delivery_report(analyses: Query, **kwargs) -> Query:
    """Return analyses that do not have a delivery report generated."""
    return analyses.filter(Analysis.delivery_report_created_at.is_(None))


def filter_report_analyses_by_pipeline(
    analyses: Query, pipeline: Pipeline = None, **kwargs
) -> Query:
    """Return the delivery report related analyses associated to the provided or supported pipelines."""
    return (
        analyses.filter(Analysis.pipeline == str(pipeline))
        if pipeline
        else analyses.filter(Analysis.pipeline.in_(REPORT_SUPPORTED_PIPELINES))
    )


def order_analyses_by_completed_at_asc(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the completed_at field."""
    return analyses.order_by(Analysis.completed_at.asc())


def order_analyses_by_uploaded_at_asc(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the uploaded_at field."""
    return analyses.order_by(Analysis.uploaded_at.asc())


def filter_analyses_by_case_entry_id(analyses: Query, case_entry_id: int, **kwargs) -> Query:
    """Return a query of analysis filtered by case entry id."""
    return analyses.filter(Analysis.family_id == case_entry_id)


def filter_analyses_started_before(analyses: Query, started_at_date: datetime, **kwargs) -> Query:
    """Return a query of analyses started before a certain date."""
    return analyses.filter(Analysis.started_at < started_at_date)


def filter_analyses_by_started_at(analyses: Query, started_at_date: datetime, **kwargs) -> Query:
    """Return a query of analyses started at a certain date."""
    return analyses.filter(Analysis.started_at == started_at_date)


def filter_analyses_not_cleaned(analyses: Query, **kwargs) -> Query:
    """Return a query of analyses that have not been cleaned."""
    return analyses.filter(Analysis.cleaned_at.is_(None))


def filter_analysis_case_action_is_none(analyses: Query, **kwargs) -> Query:
    """Return a query of analyses that do not have active cases."""
    return analyses.join(Family).filter(Family.action.is_(None))


def apply_analysis_filter(
    filter_functions: List[Callable],
    analyses: Query,
    pipeline: Pipeline = None,
    case_entry_id: int = None,
    completed_at_date: datetime = None,
    started_at_date: datetime = None,
) -> Query:
    """Apply filtering functions to the analyses queries and return filtered results."""

    for filter_function in filter_functions:
        analyses: Query = filter_function(
            analyses=analyses,
            pipeline=pipeline,
            case_entry_id=case_entry_id,
            completed_at_date=completed_at_date,
            started_at_date=started_at_date,
        )
    return analyses


class AnalysisFilter(Enum):
    """Define Analysis filter functions."""

    FILTER_VALID_IN_PRODUCTION: Callable = filter_valid_analyses_in_production
    FILTER_WITH_PIPELINE: Callable = filter_analyses_with_pipeline
    FILTER_COMPLETED: Callable = filter_completed_analyses
    FILTER_IS_UPLOADED: Callable = filter_uploaded_analyses
    FILTER_IS_NOT_UPLOADED: Callable = filter_not_uploaded_analyses
    FILTER_WITH_DELIVERY_REPORT: Callable = filter_analyses_with_delivery_report
    FILTER_WITHOUT_DELIVERY_REPORT: Callable = filter_analyses_without_delivery_report
    FILTER_REPORT_BY_PIPELINE: Callable = filter_report_analyses_by_pipeline
    FILTER_BY_CASE_ENTRY_ID: Callable = filter_analyses_by_case_entry_id
    FILTER_IS_NOT_CLEANED: Callable = filter_analyses_not_cleaned
    FILTER_STARTED_AT_BEFORE: Callable = filter_analyses_started_before
    FILTER_BY_STARTED_AT: Callable = filter_analyses_by_started_at
    FILTER_CASE_ACTION_IS_NONE: Callable = filter_analysis_case_action_is_none
    ORDER_BY_UPLOADED_AT: Callable = order_analyses_by_uploaded_at_asc
    ORDER_BY_COMPLETED_AT: Callable = order_analyses_by_completed_at_asc
