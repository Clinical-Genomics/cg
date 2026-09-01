import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from cg.exc import CgError
from cg.models.cg_config import CGConfig
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


class ExternalSampleTransferredEvent(BaseModel):
    sample_internal_id: str = Field(alias="statusdb.sample_internal_id")
    cluster_location: Path
    transfer_completed_at: datetime


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleTransferredEvent.model_validate(event_payload)
    # TODO: Take the CopyComplete into account

    if not (event.cluster_location.glob("*.bam") or event.cluster_location.glob("*fastq.gz")):
        raise CgError(f"No sequencing files found in directory {event.cluster_location}")

    sample: Sample = config.status_db.get_sample_by_internal_id_strict(event.sample_internal_id)
    config.status_db.update_external_sample(
        sample_name=sample.name,
        customer_id=sample.customer_id,
        transferred_at=event.transfer_completed_at,
    )

    config.housekeeper_api.create_new_bundle_and_version(event.sample_internal_id)

    for file in event.cluster_location.glob("*"):
        tags = [event.sample_internal_id]
        if file.as_posix().endswith(".fastq.gz"):
            tags.append("fastq")
        elif file.as_posix().endswith(".bam"):
            tags.append("bam")
        else:
            # TODO: Adress whether it should be a warning
            LOG.warning(f"File {file} has an unrecognized extension, skipping.")
            continue

        config.housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=event.sample_internal_id,
            file=file,
            tags=tags,
        )

    # TODO: Publish event that storing is complete
