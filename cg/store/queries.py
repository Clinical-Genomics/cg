import datetime as dt

from alchy import Query

from cg.store import Store, models


def get_cases_to_compress(store: Store, date_threshold: dt.datetime) -> Query:
    """Fetch all cases that are ready to be compressed by SPRING"""
    return (
        store.query(models.Family)
        .filter(models.Family.action not in ["running", "analyze"])
        .filter(models.Family.created_at < date_threshold)
        .order_by(models.Family.created_at.asc())
    )
