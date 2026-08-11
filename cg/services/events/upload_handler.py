import logging
from datetime import datetime

from cg.apps.tb.api import TrailblazerAPI
from cg.store.store import Store

LOG = logging.getLogger(__name__)

ANALYSIS_UPLOADED_SUBJECT = "analysis.upload_completed"


def completed(status_db: Store, trailblazer_api: TrailblazerAPI):
    def handler(message: dict):
        analysis_id = message["cg.analysis_id"]
        uploaded_at = message["uploaded_at"]
        try:
            uploaded_at_datetime = datetime.strptime(uploaded_at, "%Y-%m-%dT%H:%M:%SZ")
            status_db.update_analysis_uploaded_at(
                analysis_id=analysis_id,
                uploaded_at=uploaded_at_datetime,
            )
            if analysis := status_db.get_analysis_by_entry_id(analysis_id):
                trailblazer_api.set_analysis_uploaded(
                    analysis.case.internal_id, uploaded_at=uploaded_at_datetime
                )
        except Exception as error:
            LOG.error(f"Failed to update analysis uploaded_at for analysis with id {analysis_id}")
            LOG.error(f"Failed to handle message {message}.")
            LOG.exception(error)
            status_db.rollback()
            raise error

    return handler
