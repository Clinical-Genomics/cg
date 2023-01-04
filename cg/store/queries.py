import datetime as dt
from typing import List

from cg.store import Store, models
from cg.store.models import Family


def get_cases_to_compress(store: Store, date_threshold: dt.datetime) -> List[Family]:
    """Fetch all cases that are ready to be compressed by SPRING."""
    return (
        store.query(models.Family)
        .filter(models.Family.action not in ["running", "analyze"])
        .filter(models.Family.created_at < date_threshold)
        .order_by(models.Family.created_at.asc())
    )
