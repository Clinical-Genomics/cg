import logging
from datetime import datetime
from pathlib import Path

from housekeeper.store.models import Bundle, File, Version
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

    bundle: Bundle = config.housekeeper_api.add_new_bundle_and_version(event.sample_internal_id)
    version: Version = bundle.versions[0]

    files: list[File] = []
    for file_path in event.cluster_location.glob("*"):
        tags = [event.sample_internal_id]
        if file_path.as_posix().endswith(".fastq.gz"):
            tags.append("fastq")
        elif file_path.as_posix().endswith(".bam"):
            tags.append("bam")
        else:
            # TODO: Address whether it should be a warning
            LOG.warning(f"File {file_path} has an unrecognized extension, skipping.")
            continue
        file: File = config.housekeeper_api.add_file(
            path=str(file_path.absolute()), version_obj=version, tags=tags
        )
        files.append(file)
    config.housekeeper_api.finalize_file_transactions(files=files, version=version)
    config.status_db.commit_to_store()

    # TODO: Publish event that storing is complete
