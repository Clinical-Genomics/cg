from alchy import Query

from cg.constants import REPORT_SUPPORTED_PIPELINES
from cg.constants.constants import VALID_DATA_IN_PRODUCTION
from cg.store import models
from cgmodels.cg.constants import Pipeline


def filter_valid_analyses_in_production(analyses: Query, **kwargs) -> Query:
    """Fetches analyses with a valid data in production."""
    return analyses.filter(VALID_DATA_IN_PRODUCTION < models.Analysis.completed_at)


def filter_analyses_with_pipeline(analyses: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Return analyses that have been completed."""
    return analyses.filter(models.Analysis.pipeline == str(pipeline)) if pipeline else analyses


def filter_completed_analyses(analyses: Query, **kwargs) -> Query:
    """Return analyses that have been completed."""
    return analyses.filter(models.Analysis.completed_at.isnot(None))


def filter_not_completed_analyses(analyses: Query, **kwargs) -> Query:
    """Return not completed analyses."""
    return analyses.filter(models.Analysis.completed_at.is_(None))


def filter_uploaded_analyses(analyses: Query, **kwargs) -> Query:
    """Fetches analyses that have been already uploaded."""
    return analyses.filter(models.Analysis.uploaded_at.isnot(None))


def filter_not_uploaded_analyses(analyses: Query, **kwargs) -> Query:
    """Fetches analyses that have not been uploaded."""
    return analyses.filter(models.Analysis.uploaded_at.is_(None))


def filter_analyses_with_delivery_report(analyses: Query, **kwargs) -> Query:
    """Return analyses that have a delivery report generated."""
    return analyses.filter(models.Analysis.delivery_report_created_at.isnot(None))


def filter_analyses_without_delivery_report(analyses: Query, **kwargs) -> Query:
    """Return analyses that do not have a delivery report generated."""
    return analyses.filter(models.Analysis.delivery_report_created_at.is_(None))


def filter_report_analyses_by_pipeline(
    analyses: Query, pipeline: Pipeline = None, **kwargs
) -> Query:
    """Fetches the delivery report related analyses associated to the provided or supported pipelines."""
    return (
        analyses.filter(models.Analysis.pipeline == str(pipeline))
        if pipeline
        else analyses.filter(models.Analysis.pipeline.in_(REPORT_SUPPORTED_PIPELINES))
    )


def order_analyses_by_completed_at(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the completed_at field."""
    return analyses.order_by(models.Analysis.completed_at.asc())


def order_analyses_by_uploaded_at(analyses: Query, **kwargs) -> Query:
    """Return a query of ordered analyses (from old to new) by the uploaded_at field."""
    return analyses.order_by(models.Analysis.uploaded_at.asc())


def apply_analysis_filter(function: str, analyses: Query, pipeline: Pipeline = None) -> Query:
    """Apply filtering functions to the analyses queries and return filtered results."""

    filter_map = {
        "valid_analyses_in_production": filter_valid_analyses_in_production,
        "analyses_with_pipeline": filter_analyses_with_pipeline,
        "completed_analyses": filter_completed_analyses,
        "not_completed_analyses": filter_not_completed_analyses,
        "uploaded_analyses": filter_uploaded_analyses,
        "not_uploaded_analyses": filter_not_uploaded_analyses,
        "analyses_with_delivery_report": filter_analyses_with_delivery_report,
        "analyses_without_delivery_report": filter_analyses_without_delivery_report,
        "filter_report_analyses_by_pipeline": filter_report_analyses_by_pipeline,
        "order_analyses_by_completed_at": order_analyses_by_completed_at,
        "order_analyses_by_uploaded_at": order_analyses_by_uploaded_at,
    }

    return filter_map[function](analyses=analyses, pipeline=pipeline)
