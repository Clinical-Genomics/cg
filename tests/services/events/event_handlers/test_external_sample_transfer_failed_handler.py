from datetime import datetime
from unittest.mock import create_autospec

from mock import Mock
from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig, SlackWebhooks
from cg.services.events.constants import (
    EXTERNAL_SAMPLE_TRANSFER_FAILED_EVENT,
    SAMPLE_INTERNAL_ID_FIELD,
)
from cg.services.events.event_handlers import external_sample_transfer_failed_handler
from cg.services.events.event_handlers.external_sample_transfer_failed_handler import (
    slack_notification_service,
    transfer_to_cluster_service,
)
from cg.services.events.event_metadata import EventMetadata, EventSequence
from cg.store.models import Sample
from cg.store.store import Store


def test_handle_failure_successfully(mocker: MockerFixture):
    # event, metadata
    status_db = create_autospec(Store)
    sample = create_autospec(Sample)
    status_db.get_sample_by_internal_id_strict = Mock(return_value=sample)
    config = create_autospec(
        CGConfig,
        status_db=status_db,
        slack_webhooks=SlackWebhooks(
            sysdev_team="https://sys-dev.team", prod_team="https://production-dev.team"
        ),
    )

    event_payload = {
        SAMPLE_INTERNAL_ID_FIELD: "ACC123",
        "transfer_failed_at": "2026-10-02T13:32:27",
    }
    metadata = EventMetadata(
        sequence=EventSequence(consumer=1, stream=1),
        num_pending=1,
        num_delivered=1,
        timestamp=datetime.now(),
        stream="cg-test",
        consumer="cluster-consumer",
    )

    transfer_to_cluster_mock = mocker.patch.object(transfer_to_cluster_service, "transfer_sample")

    slack_notification_mock = mocker.patch.object(slack_notification_service, "notify")

    # start another rsync job using transfer to cluster service
    external_sample_transfer_failed_handler.handle(
        config=config, event_payload=event_payload, event_metadata=metadata
    )

    # THEN a new rsync job should have been sent out
    transfer_to_cluster_mock.assert_called_once_with(cg_config=config, sample=sample)

    # THEN a Slack notification have been sent out
    calls = slack_notification_mock.call_args_list
    first_call = calls[0]
    assert first_call.kwargs["recipient"] == "https://sys-dev.team"
    assert first_call.kwargs["notification"].title == "Failed to RSYNC external sample to cluster"
    assert (
        first_call.kwargs["notification"].message
        == f"Message 1: `{EXTERNAL_SAMPLE_TRANSFER_FAILED_EVENT}` failed for sample `ACC123`"
    )
