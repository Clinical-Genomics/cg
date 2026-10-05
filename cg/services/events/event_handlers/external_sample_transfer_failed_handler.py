from datetime import datetime

from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig
from cg.services import slack_notification_service, transfer_to_cluster_service
from cg.services.events.constants import (
    EXTERNAL_SAMPLE_TRANSFER_FAILED_EVENT,
    SAMPLE_INTERNAL_ID_FIELD,
)
from cg.services.events.event_metadata import EventMetadata
from cg.services.slack_notification_service import SlackNotification
from cg.store.models import Sample

MAX_RETRIES = 5


class ExternalSampleTransferFailedEvent(BaseModel):
    sample_internal_id: str = Field(alias=SAMPLE_INTERNAL_ID_FIELD)
    transfer_failed_at: datetime
    log_dir: str
    number_of_retries: int


def handle(config: CGConfig, event_payload: dict, event_metadata: EventMetadata):
    event = ExternalSampleTransferFailedEvent.model_validate(event_payload)
    if event.number_of_retries >= MAX_RETRIES:
        slack_notification_service.notify(
            recipient=config.slack_webhooks.sysdev_team,
            notification=SlackNotification(
                title="Final attempt to RSYNC external sample to cluster failed",
                message=f"Message {event_metadata.sequence.stream}: `{EXTERNAL_SAMPLE_TRANSFER_FAILED_EVENT}` failed for sample `{event.sample_internal_id}` at {event.transfer_failed_at}.\nSee the logs in: `{event.log_dir}`. Will not try further",
            ),
        )
    else:
        sample: Sample = config.status_db.get_sample_by_internal_id_strict(
            internal_id=event.sample_internal_id
        )
        number_of_retries = event.number_of_retries + 1
        slack_notification_service.notify(
            recipient=config.slack_webhooks.sysdev_team,
            notification=SlackNotification(
                title="Failed to RSYNC external sample to cluster",
                message=f"Message {event_metadata.sequence.stream}: `{EXTERNAL_SAMPLE_TRANSFER_FAILED_EVENT}`\nAttempt {number_of_retries} of {MAX_RETRIES} failed for sample `{event.sample_internal_id}` at `{event.transfer_failed_at}`.\nSee the logs in: {event.log_dir}",
            ),
        )
        transfer_to_cluster_service.transfer_sample(
            cg_config=config, sample=sample, number_of_retries=number_of_retries
        )
