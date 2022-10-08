from typing import Optional

from alchy import Query
from sqlalchemy import and_, or_

from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY
from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.observations import LOQUSDB_SUPPORTED_PIPELINES
from cg.store import models


def filter_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Return cases that is not sequenced according to record in StatusDB."""
    return cases.filter(or_(models.Application.is_external, models.Sample.sequenced_at.isnot(None)))


def filter_cases_with_pipeline(cases: Query, pipeline: str = None, **kwargs) -> Query:
    """Return cases with pipeline."""
    return cases.filter(models.Family.data_analysis == pipeline) if pipeline else cases


def filter_cases_with_loqusdb_supported_pipeline(
    cases: Query, pipeline: str = None, **kwargs
) -> Query:
    """Return loqusdb related cases with pipeline."""
    records: Query = (
        cases.filter(models.Family.data_analysis == pipeline)
        if pipeline
        else cases.filter(models.Family.data_analysis.in_(LOQUSDB_SUPPORTED_PIPELINES))
    )

    return records.filter(models.Customer.loqus_upload == True)


def filter_cases_for_analysis(cases: Query, **kwargs) -> Query:
    """Return cases in need of analysis by:
    1. Action set to analyze or
    2. Internally created cases with no action set and no prior analysis or
    3. Cases with no action, but new sequence data
    """
    return cases.filter(
        or_(
            models.Family.action == CaseActions.ANALYZE,
            and_(
                models.Application.is_external.isnot(True),
                models.Family.action.is_(None),
                models.Analysis.created_at.is_(None),
            ),
            and_(
                models.Family.action.is_(None),
                models.Analysis.created_at < models.Sample.sequenced_at,
            ),
        )
    )


def filter_cases_with_scout_data_delivery(cases: Query, **kwargs) -> Query:
    """Return cases containing Scout as a data delivery option."""
    return cases.filter(models.Family.data_delivery.contains(DataDelivery.SCOUT))


def filter_report_supported_data_delivery_cases(cases: Query, **kwargs) -> Query:
    """Extracts cases with a valid data delivery for delivery report generation."""
    return cases.filter(models.Family.data_delivery.in_(REPORT_SUPPORTED_DATA_DELIVERY))


def apply_case_filter(function: str, cases: Query, pipeline: Optional[str] = None):
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "cases_has_sequence": filter_cases_has_sequence,
        "cases_with_pipeline": filter_cases_with_pipeline,
        "cases_with_loqusdb_supported_pipeline": filter_cases_with_loqusdb_supported_pipeline,
        "filter_cases_for_analysis": filter_cases_for_analysis,
        "cases_with_scout_data_delivery": filter_cases_with_scout_data_delivery,
        "filter_report_cases_with_valid_data_delivery": filter_report_supported_data_delivery_cases,
    }
    return filter_map[function](cases=cases, pipeline=pipeline)
