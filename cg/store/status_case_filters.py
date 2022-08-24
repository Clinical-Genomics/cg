from alchy import Query
from sqlalchemy import and_, or_

from cg.constants.constants import CaseActions
from cg.store import models


def filter_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Return cases that is not sequenced according to record in StatusDB"""
    return cases.filter(or_(models.Application.is_external, models.Sample.sequenced_at.isnot(None)))


def filter_cases_with_pipeline(cases: Query, pipeline: str, **kwargs) -> Query:
    """Return cases with pipeline"""
    return cases.filter(models.Family.data_analysis == pipeline)


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


def apply_filter(function: str, pipeline: str, cases: Query):
    """Apply filtering functions and return filtered results"""
    filter_map = {
        "cases_has_sequence": filter_cases_has_sequence,
        "cases_with_pipeline": filter_cases_with_pipeline,
        "filter_cases_for_analysis": filter_cases_for_analysis,
    }
    return filter_map[function](cases=cases, pipeline=pipeline)
