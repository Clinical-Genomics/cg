from alchy import Query
from sqlalchemy import and_, or_
from typing import Dict

from cg.store import models


def filter_cases_has_sequence(cases: Query, **kwargs) -> Query:
    """Return cases that is not sequenced according to recorded in StstusDB"""
    return cases.filter(or_(models.Application.is_external, models.Sample.sequenced_at.isnot(None)))


def filter_cases_with_pipeline(cases: Query, pipeline: str, **kwargs) -> Query:
    """Return cases with pipeline"""
    return cases.filter(models.Family.data_analysis == pipeline)


def apply_filter(function: str, pipeline: str, cases: Query):
    """Apply filtering functions and return filtered results"""
    filter_map = {
        "cases_has_sequence": filter_cases_has_sequence,
        "cases_with_pipeline": filter_cases_with_pipeline,
    }
    return filter_map[function](cases=cases, pipeline=pipeline)
