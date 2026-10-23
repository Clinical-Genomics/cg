import logging
from datetime import datetime

from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig
from cg.services.events.constants import ANALYSIS_ID_FIELD
from cg.services.events.event_metadata import EventMetadata

LOG = logging.getLogger(__name__)


class AnalysisUploadedEvent(BaseModel):
    analysis_id: int = Field(alias=ANALYSIS_ID_FIELD)
    uploaded_at: datetime


def handle(config: CGConfig, event_payload: dict, event_metadata: EventMetadata) -> None:
    event = AnalysisUploadedEvent.model_validate(event_payload)

    if analysis := config.status_db.get_analysis_by_entry_id_strict(event.analysis_id):
        analysis.uploaded_at = event.uploaded_at

        config.trailblazer_api.set_analysis_uploaded(
            analysis.case.internal_id, uploaded_at=event.uploaded_at
        )

        LOG.info(f"Case {analysis.case.internal_id} set as uploaded in Trailblazer.")
