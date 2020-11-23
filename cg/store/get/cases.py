"""Functions to get cases from the store database"""

from typing import Iterator

import datetime as dt

from cg.store import models
from cg.store.api import Store


def ready_for_spring_compression(
    store: Store, date_threshold: dt.datetime
) -> Iterator[models.Family]:
    """Fetch all cases that are ready to be compressed by SPRING"""
    cases = (
        store.Family.query.filter(models.Family.created_at < date_threshold)
        .filter(models.Family.action.notin_(["running", "analyze"]))
        .order_by(models.Family.created_at.asc())
    )
    for case_obj in cases:
        yield case_obj
