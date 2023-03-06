from datetime import datetime
from typing import Optional, List

from cgmodels.cg.constants import Pipeline
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY
from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.observations import (
    LOQUSDB_SUPPORTED_PIPELINES,
    LOQUSDB_MIP_SEQUENCING_METHODS,
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
)
from cg.store.models import Analysis, Application, Customer, Family, Sample


def get_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Return cases that is not sequenced according to record in StatusDB."""
    return cases.filter(or_(Application.is_external, Sample.sequenced_at.isnot(None)))


def get_inactive_analysis_cases(cases: Query, **kwargs) -> Query:
    """Return cases which are not set or on hold."""
    return cases.filter(
        or_(
            Family.action.is_(None),
            Family.action == CaseActions.HOLD,
        )
    )


def get_new_cases(cases: Query, date: datetime, **kwargs) -> Query:
    """Return old cases compared to date."""
    cases = cases.filter(Family.created_at < date)
    return cases.order_by(Family.created_at.asc())


def get_cases_with_pipeline(cases: Query, pipeline: Pipeline = None, **kwargs) -> Query:
    """Return cases with pipeline."""
    return cases.filter(Family.data_analysis == pipeline) if pipeline else cases


def get_cases_with_loqusdb_supported_pipeline(
    cases: Query, pipeline: Pipeline = None, **kwargs
) -> Query:
    """Return Loqusdb related cases with pipeline."""
    records: Query = (
        cases.filter(Family.data_analysis == pipeline)
        if pipeline
        else cases.filter(Family.data_analysis.in_(LOQUSDB_SUPPORTED_PIPELINES))
    )

    return records.filter(Customer.loqus_upload == True)


def get_cases_with_loqusdb_supported_sequencing_method(
    cases: Query, pipeline: Pipeline = None, **kwargs
) -> Query:
    """Return cases with Loqusdb supported sequencing method."""
    supported_sequencing_methods = {
        Pipeline.MIP_DNA: LOQUSDB_MIP_SEQUENCING_METHODS,
        Pipeline.BALSAMIC: LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
    }
    return (
        cases.filter(Application.prep_category.in_(supported_sequencing_methods[pipeline]))
        if pipeline
        else cases
    )


def get_cases_for_analysis(cases: Query, **kwargs) -> Query:
    """Return cases in need of analysis by:
    1. Action set to analyze or
    2. Internally created cases with no action set and no prior analysis or
    3. Cases with no action, but new sequence data
    """
    return cases.filter(
        or_(
            Family.action == CaseActions.ANALYZE,
            and_(
                Application.is_external.isnot(True),
                Family.action.is_(None),
                Analysis.created_at.is_(None),
            ),
            and_(
                Family.action.is_(None),
                Analysis.created_at < Sample.sequenced_at,
            ),
        )
    )


def get_cases_with_scout_data_delivery(cases: Query, **kwargs) -> Query:
    """Return cases containing Scout as a data delivery option."""
    return cases.filter(Family.data_delivery.contains(DataDelivery.SCOUT))


def get_report_supported_data_delivery_cases(cases: Query, **kwargs) -> Query:
    """Return cases with a valid data delivery for delivery report generation."""
    return cases.filter(Family.data_delivery.in_(REPORT_SUPPORTED_DATA_DELIVERY))


def apply_case_filter(
    cases: Query,
    functions: List[str],
    date: Optional[datetime] = None,
    pipeline: Optional[Pipeline] = None,
) -> Query:
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "get_cases_for_analysis": get_cases_for_analysis,
        "get_cases_has_sequence": get_cases_has_sequence,
        "get_cases_with_loqusdb_supported_pipeline": get_cases_with_loqusdb_supported_pipeline,
        "get_cases_with_loqusdb_supported_sequencing_method": get_cases_with_loqusdb_supported_sequencing_method,
        "get_cases_with_pipeline": get_cases_with_pipeline,
        "get_cases_with_scout_data_delivery": get_cases_with_scout_data_delivery,
        "get_inactive_analysis_cases": get_inactive_analysis_cases,
        "get_new_cases": get_new_cases,
        "get_report_cases_with_valid_data_delivery": get_report_supported_data_delivery_cases,
    }
    for function in functions:
        cases: Query = filter_map[function](cases=cases, date=date, pipeline=pipeline)
    return cases
