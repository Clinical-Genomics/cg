import logging
from datetime import datetime

from cg.store.store import Store

LOG = logging.getLogger(__name__)


def completed(store: Store):
    def handler(message: dict):
        try:
            store.update_analysis_uploaded_at(
                analysis_id=message["cg.analysis_id"],
                uploaded_at=datetime.strptime(message["uploaded_at"], "%Y-%m-%dT%H:%M:%SZ"),
            )
        except Exception as error:
            LOG.exception(error)

    return handler
