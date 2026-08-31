import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class ExternalSampleTransferredEvent(BaseModel):
    sample_internal_id: str = Field(alias="cg.sample_internal_id")
    cluster_location: Path
    transfer_completed_at: datetime


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleTransferredEvent.model_validate(event_payload)
    # TODO: Get bundle name and tags
    for file in event.cluster_location.glob("*"):
        tags = [event.sample_internal_id]
        if file.as_posix().endswith(".fastq.gz"):
            tags.append("fastq")
        elif file.as_posix().endswith(".bam"):
            tags.append("bam")
        else:
            LOG.warning(f"File {file} has an unrecognized extension, skipping.")

    # TODO: Call Housekeeper API to add file

    # TODO: Publish event that storing is complete
