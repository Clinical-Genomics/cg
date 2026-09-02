import logging
from datetime import datetime
from pathlib import Path

from housekeeper.store.models import Bundle, File, Version
from pydantic import BaseModel, Field

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CgError
from cg.models.cg_config import CGConfig
from cg.services.events import event_publisher
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
EXTERNAL_SAMPLE_STORED_SUBJECT = "external_sample.storage_completed"


class ExternalSampleTransferredEvent(BaseModel):
    sample_internal_id: str = Field(alias="statusdb.sample_internal_id")
    cluster_location: Path
    transfer_completed_at: datetime


def handle(config: CGConfig, event_payload: dict) -> None:
    """
    Add all sequencing files for the sample in the payload to the Housekeeper database
    and copy them to the corresponding Housekeeper bundle directory. Also update the entry for the
    sample in the ExternalSample table with the datetime of the transfer.
    """
    event = ExternalSampleTransferredEvent.model_validate(event_payload)

    if not (event.cluster_location.glob("*.bam") or event.cluster_location.glob("*fastq.gz")):
        raise CgError(f"No sequencing files found in directory {event.cluster_location}")

    sample: Sample = config.status_db.get_sample_by_internal_id_strict(event.sample_internal_id)
    config.status_db.update_external_sample(
        sample_name=sample.name,
        customer_id=sample.customer_id,
        transferred_at=event.transfer_completed_at,
    )
    LOG.info(
        f"Updated transferred_at for ExternalSample {sample.name} of customer {sample.customer_id} "
        f"to {event.transfer_completed_at}."
    )

    _add_sample_files_to_housekeeper(housekeeper_api=config.housekeeper_api, event=event)
    config.status_db.commit_to_store()
    event_publisher.publish(
        nats_config=config.nats,
        subject=f"{config.nats.stream}.{EXTERNAL_SAMPLE_STORED_SUBJECT}",
        event_payload={"statusdb.sample_internal_id": event.sample_internal_id},
    )


def _add_sample_files_to_housekeeper(
    housekeeper_api: HousekeeperAPI, event: ExternalSampleTransferredEvent
):
    bundle: Bundle = housekeeper_api.add_new_bundle_and_version(event.sample_internal_id)
    version: Version = bundle.versions[0]

    files: list[File] = []
    for file_path in event.cluster_location.glob("*"):
        tags = [event.sample_internal_id]
        if file_path.as_posix().endswith(".fastq.gz"):
            tags.append("fastq")
        elif file_path.as_posix().endswith(".bam"):
            tags.append("bam")
        else:
            LOG.info(f"Omitting storing for non-sequencing file {file_path}.")
            continue
        file: File = housekeeper_api.add_file(
            path=str(file_path.absolute()), version_obj=version, tags=tags
        )
        files.append(file)
    housekeeper_api.finalize_file_transactions(files=files, version=version)
