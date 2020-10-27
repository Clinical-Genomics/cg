"""Store functions used in delivery"""

import logging

from typing import Iterable

from cg.store import Store
from cg.store.models import Analysis

LOG = logging.getLogger(__name__)


def suggest_cases_to_deliver(store: Store, pipeline: str = None) -> Iterable[Analysis]:
    LOG.info("Fetching the last 50 cases with pipeline: %s", pipeline)
    pipeline = pipeline or ""
    return store.analyses_to_deliver(pipeline=pipeline, limit=50)
