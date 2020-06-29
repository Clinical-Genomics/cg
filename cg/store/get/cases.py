"""Functions to get cases from the store database"""

from typing import Iterator

from sqlalchemy.orm import Query

from cg.store import models
from cg.store.api import Store


def analysis_completed(store: Store) -> Query:
    """Return cases where analysis is finished"""
    cases = store.Family.query.join(models.Analysis)
    return cases.filter(models.Analysis.completed_at.isnot(None))


def ready_for_spring_compresssion(store: Store) -> Iterator[models.Family]:
    """Fetch all cases that are ready to be compressed by SPRING"""
    for case_obj in analysis_completed(store):
        if case_obj.ordered_at > case_obj.analyses[0].completed_at:
            continue
        yield case_obj
