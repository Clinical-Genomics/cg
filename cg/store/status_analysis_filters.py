from typing import List

from sqlalchemy.orm import Query

from cg.constants import REPORT_SUPPORTED_PIPELINES
from cg.constants.constants import VALID_DATA_IN_PRODUCTION
from cg.store.models import Analysis
from cgmodels.cg.constants import Pipeline


def get_valid_analyses_in_production(analyses: Query, **kwargs) -> Query:
    """Return analyses with a valid data in production."""
    return analyses.filter(VALID_DATA_IN_PRODUCTION < Analysis.completed_at)


def get_analyses_with_pipeline(analyses: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Return analyses with suplied pipeline."""
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
    functions: List[str], analyses: Query, pipeline: Pipeline = None
) -> Query:
    """Apply filtering functions to the analyses queries and return filtered results."""
    filter_map = {
        "get_analyses_with_delivery_report": get_analyses_with_delivery_report,
        "get_analyses_without_delivery_report": get_analyses_without_delivery_report,
        "get_analyses_with_pipeline": get_analyses_with_pipeline,
        "get_completed_analyses": get_completed_analyses,
        "get_filter_uploaded_analyses": get_filter_uploaded_analyses,
        "get_not_completed_analyses": get_not_completed_analyses,
        "get_not_uploaded_analyses": get_not_uploaded_analyses,
        "get_report_analyses_by_pipeline": get_report_analyses_by_pipeline,
        "get_valid_analyses_in_production": get_valid_analyses_in_production,
        "order_analyses_by_completed_at": order_analyses_by_completed_at,
        "order_analyses_by_uploaded_at": order_analyses_by_uploaded_at,
    }
    for function in functions:
        analyses: Query = filter_map[function](analyses=analyses, pipeline=pipeline)
    return analyses
