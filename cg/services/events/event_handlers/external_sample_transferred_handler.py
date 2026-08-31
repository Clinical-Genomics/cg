import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cg.exc import CgError
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class ExternalSampleTransferredEvent(BaseModel):
    sample_internal_id: str = Field(alias="cg.sample_internal_id")
    cluster_location: Path
    transfer_completed_at: datetime


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleTransferredEvent.model_validate(event_payload)

    if not any(event.cluster_location.iterdir()):
        raise CgError(f"Directory {event.cluster_location} is empty.")

    config.housekeeper_api.create_new_bundle_and_version(event.sample_internal_id)

    for file in event.cluster_location.glob("*"):
        tags = [event.sample_internal_id]
        if file.as_posix().endswith(".fastq.gz"):
            tags.append("fastq")
        elif file.as_posix().endswith(".bam"):
            tags.append("bam")
        else:
            LOG.warning(f"File {file} has an unrecognized extension, skipping.")

        config.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=event.sample_internal_id,
            file=file,
            tags=tags,
        )

    # TODO: Publish event that storing is complete
