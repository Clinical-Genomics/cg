from datetime import datetime
from typing import Optional

from alchy import Query
from cgmodels.cg.constants import Pipeline
from sqlalchemy import and_, or_

from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY
from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.observations import (
    LOQUSDB_SUPPORTED_PIPELINES,
    LOQUSDB_MIP_SEQUENCING_METHODS,
    LOQUSDB_BALSAMIC_SEQUENCING_METHODS,
)
from cg.store.models import Analysis, Application, Customer, Family, Sample


def filter_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Return cases that is not sequenced according to record in StatusDB."""
    return cases.filter(or_(Application.is_external, Sample.sequenced_at.isnot(None)))


def filter_inactive_analysis_cases(cases: Query, **kwargs) -> Query:
    """Return cases which are not set or on hold."""
    return cases.filter(
        or_(
            Family.action.is_(None),
            Family.action.is_(CaseActions.HOLD),
        )
    )


def filter_new_cases(cases: Query, date: datetime, **kwargs) -> Query:
    """Return old cases compared to date."""
    cases = cases.filter(Family.created_at < date)
    return cases.order_by(Family.created_at.asc())


def filter_cases_with_pipeline(cases: Query, pipeline: str = None, **kwargs) -> Query:
    """Return cases with pipeline."""
    return cases.filter(Family.data_analysis == pipeline) if pipeline else cases


def filter_cases_with_loqusdb_supported_pipeline(
    cases: Query, pipeline: str = None, **kwargs
) -> Query:
    """Return Loqusdb related cases with pipeline."""
    records: Query = (
        cases.filter(Family.data_analysis == pipeline)
        if pipeline
        else cases.filter(Family.data_analysis.in_(LOQUSDB_SUPPORTED_PIPELINES))
    )

    return records.filter(Customer.loqus_upload == True)


def filter_cases_with_loqusdb_supported_sequencing_method(
    cases: Query, pipeline: str = None, **kwargs
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


def filter_cases_for_analysis(cases: Query, **kwargs) -> Query:
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


def filter_cases_with_scout_data_delivery(cases: Query, **kwargs) -> Query:
    """Return cases containing Scout as a data delivery option."""
    return cases.filter(Family.data_delivery.contains(DataDelivery.SCOUT))


def filter_report_supported_data_delivery_cases(cases: Query, **kwargs) -> Query:
    """Extracts cases with a valid data delivery for delivery report generation."""
    return cases.filter(Family.data_delivery.in_(REPORT_SUPPORTED_DATA_DELIVERY))


def apply_case_filter(
    function: str, cases: Query, date: Optional[datetime] = None, pipeline: Optional[str] = None
):
    """Apply filtering functions and return filtered results."""
    filter_map = {
        "cases_has_sequence": filter_cases_has_sequence,
        "cases_with_pipeline": filter_cases_with_pipeline,
        "cases_with_loqusdb_supported_pipeline": filter_cases_with_loqusdb_supported_pipeline,
        "cases_with_loqusdb_supported_sequencing_method": filter_cases_with_loqusdb_supported_sequencing_method,
        "filter_cases_for_analysis": filter_cases_for_analysis,
        "cases_with_scout_data_delivery": filter_cases_with_scout_data_delivery,
        "filter_report_cases_with_valid_data_delivery": filter_report_supported_data_delivery_cases,
        "inactive_analysis_cases": filter_inactive_analysis_cases,
        "new_cases": filter_new_cases,
    }
    return filter_map[function](cases=cases, date=date, pipeline=pipeline)
