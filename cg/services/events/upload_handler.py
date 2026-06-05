import logging
from datetime import datetime

from cg.store.store import Store

LOG = logging.getLogger(__name__)

ANALYSIS_UPLOADED_SUBJECT = "analysis.upload_completed"


def completed(store: Store):
    def handler(message: dict):
        analysis_id = message["cg.analysis_id"]
        uploaded_at = message["uploaded_at"]
        try:
            store.update_analysis_uploaded_at(
                analysis_id=analysis_id,
                uploaded_at=datetime.strptime(uploaded_at, "%Y-%m-%dT%H:%M:%SZ"),
            )
        except Exception as error:
            LOG.error(f"Failed to update analysis uploaded_at for analysis with id {analysis_id}")
            LOG.error(f"Failed to handle message {message}.")
            LOG.exception(error)

    return handler
