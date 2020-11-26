"""Functions to get cases from the store database"""

from alchy import Query
import datetime as dt

from cg.store import models
from cg.store.api import Store


def ready_for_spring_compression(store: Store, date_threshold: dt.datetime) -> Query:
    """Fetch all cases that are ready to be compressed by SPRING"""
    cases = (
        store.query(models.Family)
        .filter(models.Family.action not in ["running", "analyze"])
        .filter(models.Family.created_at < date_threshold)
        .order_by(models.Family.created_at.asc())
    )

    return cases
