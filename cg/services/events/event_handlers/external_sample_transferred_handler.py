from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig


class ExternalSampleTransferredEvent(BaseModel):
    sample_internal_id: str = Field(alias="cg.sample_internal_id")
    cluster_location: Path
    transfer_completed_at: datetime


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleTransferredEvent.model_validate(event_payload)
    # TODO: Get bundle name and tags

    # TODO: Call Housekeeper API to add file

    # TODO: Publish event that storing is complete
