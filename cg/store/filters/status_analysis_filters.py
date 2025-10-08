from datetime import datetime
from enum import Enum
from typing import Callable

from sqlalchemy import and_
from sqlalchemy.orm import Query

from cg.constants import REPORT_SUPPORTED_WORKFLOW
from cg.constants.constants import VALID_DATA_IN_PRODUCTION, Workflow
from cg.store.models import Analysis, Case


def filter_valid_analyses_in_production(analyses: Query, **kwargs) -> Query:
    """Return analyses with a valid data in production."""
    return analyses.filter(VALID_DATA_IN_PRODUCTION < Analysis.completed_at)


def filter_analyses_with_workflow(analyses: Query, workflow: Workflow = None, **kwargs) -> Query:
    """Return analyses with supplied workflow."""
    return analyses.filter(Analysis.workflow == workflow) if workflow else analyses


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


def filter_report_analyses_by_workflow(
    analyses: Query, workflow: Workflow = None, **kwargs
) -> Query:
    """Return the delivery report related analyses associated to the provided or supported workflows."""
    return (
        analyses.filter(Analysis.workflow == workflow)
        if workflow
        else analyses.filter(Analysis.workflow.in_(REPORT_SUPPORTED_WORKFLOW))
    )


def order_analyses_by_completed_at_asc(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the completed_at field."""
    return analyses.order_by(Analysis.completed_at.asc())


def order_analyses_by_uploaded_at_asc(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the uploaded_at field."""
    return analyses.order_by(Analysis.uploaded_at.asc())


def filter_analyses_started_before(analyses: Query, started_at_date: datetime, **kwargs) -> Query:
    """Return a query of analyses started before a certain date."""
    return analyses.filter(Analysis.started_at < started_at_date)


def filter_analyses_completed_before(
    analyses: Query, completed_at_date: datetime, **kwargs
) -> Query:
    """Return a query of analyses completed before a certain date."""
    return analyses.filter(
        and_(
            Analysis.completed_at.isnot(None),
            Analysis.completed_at < completed_at_date,
        )
    )


def filter_analyses_not_cleaned(analyses: Query, **kwargs) -> Query:
    """Return a query of analyses that have not been cleaned."""
    return analyses.filter(Analysis.cleaned_at.is_(None))


def filter_analysis_case_action_is_none(analyses: Query, **kwargs) -> Query:
    """Return a query of analyses that do not have active cases."""
    return analyses.join(Case).filter(Case.action.is_(None))


def filter_analysis_by_entry_id(analyses: Query, entry_id: int, **kwargs) -> Query:
    """Return a query of analyses filtered by entry id."""
    return analyses.filter(Analysis.id == entry_id)


def apply_analysis_filter(
    filter_functions: list[Callable],
    analyses: Query,
    case_entry_id: int = None,
    completed_at_date: datetime = None,
    entry_id: int = None,
    started_at_date: datetime = None,
    workflow: Workflow = None,
) -> Query:
    """Apply filtering functions to the analyses queries and return filtered results."""

    for filter_function in filter_functions:
        analyses: Query = filter_function(
            analyses=analyses,
            workflow=workflow,
            case_entry_id=case_entry_id,
            completed_at_date=completed_at_date,
            entry_id=entry_id,
            started_at_date=started_at_date,
        )
    return analyses


class AnalysisFilter(Enum):
    """Define Analysis filter functions."""

    VALID_IN_PRODUCTION: Callable = filter_valid_analyses_in_production
    WITH_WORKFLOW: Callable = filter_analyses_with_workflow
    COMPLETED: Callable = filter_completed_analyses
    IS_UPLOADED: Callable = filter_uploaded_analyses
    IS_NOT_UPLOADED: Callable = filter_not_uploaded_analyses
    WITH_DELIVERY_REPORT: Callable = filter_analyses_with_delivery_report
    WITHOUT_DELIVERY_REPORT: Callable = filter_analyses_without_delivery_report
    REPORT_BY_WORKFLOW: Callable = filter_report_analyses_by_workflow
    IS_NOT_CLEANED: Callable = filter_analyses_not_cleaned
    STARTED_AT_BEFORE: Callable = filter_analyses_started_before
    COMPLETED_AT_BEFORE: Callable = filter_analyses_completed_before
    CASE_ACTION_IS_NONE: Callable = filter_analysis_case_action_is_none
    ORDER_BY_UPLOADED_AT: Callable = order_analyses_by_uploaded_at_asc
    ORDER_BY_COMPLETED_AT: Callable = order_analyses_by_completed_at_asc
    BY_ENTRY_ID: Callable = filter_analysis_by_entry_id
