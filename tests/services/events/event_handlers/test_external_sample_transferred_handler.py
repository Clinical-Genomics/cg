from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, call, create_autospec

import pytest
from housekeeper.store.models import Bundle, Version
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CgError
from cg.models.cg_config import CGConfig, NatsConfig, SlackWebhooks
from cg.services.events.constants import (
    EXTERNAL_SAMPLE_STORED_EVENT,
    EXTERNAL_SAMPLE_TRANSFERRED_EVENT,
    SAMPLE_INTERNAL_ID_FIELD,
)
from cg.services.events.event_handlers import external_sample_transferred_handler
from cg.services.events.event_handlers.external_sample_transferred_handler import (
    shutil,
    slack_notification_service,
)
from cg.store.models import Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_handle_success(mocker: MockerFixture):
    # GIVEN a StatusDB
    status_db: TypedMock[Store] = create_typed_mock(Store)
    sample: Sample = create_autospec(Sample, customer_id=1)
    sample.name = "sample-name"
    status_db.as_type.get_sample_by_internal_id_strict = Mock(return_value=sample)

    # GIVEN a HousekeeperAPI
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    version = create_autospec(Version)
    bundle = create_autospec(Bundle, versions=[version])
    housekeeper_api.as_type.add_new_bundle_and_version = Mock(return_value=bundle)

    # GIVEN a NATS configuration
    nats_config: NatsConfig = create_autospec(NatsConfig, stream="cg-test")

    # GIVEN a CG config
    config: CGConfig = create_autospec(
        CGConfig,
        status_db=status_db.as_type,
        housekeeper_api=housekeeper_api.as_type,
        nats=nats_config,
    )

    # GIVEN a publisher for completion events
    publish_mock = mocker.patch.object(
        external_sample_transferred_handler.event_publisher, "publish_event"
    )

    # GIVEN a valid event payload
    event_payload = {
        SAMPLE_INTERNAL_ID_FIELD: "ACC123",
        "cluster_location": "/path/to/mirrored/sample",
        "transfer_completed_at": "2026-08-31T14:41:00",
    }

    # GIVEN that two files have been transferred for the given sample
    path_r1 = Path("file_R1.fastq.gz")
    path_r2 = Path("file_R2.fastq.gz")
    mocker.patch.object(Path, "glob", return_value=[path_r1, path_r2])

    # GIVEN that deleting the directory goes fine
    rmtree_mock = mocker.patch.object(shutil, "rmtree")

    # WHEN calling handle
    external_sample_transferred_handler.handle(config=config, event_payload=event_payload)

    # THEN the external sample transferred_at was set
    expected_datetime = datetime(year=2026, month=8, day=31, hour=14, minute=41)
    status_db.as_mock.update_external_sample.assert_called_once_with(
        sample_name="sample-name", customer_id=1, transferred_at=expected_datetime
    )

    # THEN a housekeeper bundle and version was created for the sample
    housekeeper_api.as_mock.add_new_bundle_and_version.assert_called_once_with("ACC123")

    # THEN all sequencing files were added to the bundle
    r1_call = call(path=str(path_r1.absolute()), version_obj=version, tags=["ACC123", "fastq"])
    r2_call = call(path=str(path_r2.absolute()), version_obj=version, tags=["ACC123", "fastq"])
    function_calls: list = housekeeper_api.as_mock.add_file.call_args_list
    assert r1_call in function_calls
    assert r2_call in function_calls
    assert len(function_calls) == 2

    # THEN the changes were commited so that we can be certain that they are there when the next
    # event is received
    status_db.as_mock.commit_to_store.assert_called_once()

    # THEN an event was published saying the sample was stored
    publish_mock.assert_called_once_with(
        nats_config=nats_config,
        event_name=EXTERNAL_SAMPLE_STORED_EVENT,
        event_payload={SAMPLE_INTERNAL_ID_FIELD: "ACC123"},
    )

    # THEN the mirrored sample folder was deleted
    rmtree_mock.assert_called_once_with(Path("/path/to/mirrored/sample"))


def test_handle_failure(mocker: MockerFixture):
    # GIVEN a CG config
    config: CGConfig = create_autospec(
        CGConfig,
        status_db=create_autospec(Store),
        housekeeper_api=create_autospec(HousekeeperAPI),
        nats=create_autospec(NatsConfig),
        slack_webhooks=SlackWebhooks(prod_team="http.bingus.gov"),
    )

    # GIVEN that there is no *.bam or *.fastq.gz in the cluster location
    mocker.patch.object(Path, "glob", return_value=[])

    # GIVEN a valid event payload
    event_payload = {
        SAMPLE_INTERNAL_ID_FIELD: "ACC123",
        "cluster_location": "/cluster_location",
        "transfer_completed_at": "2026-08-31T14:41:00",
    }

    # GIVEN a Slack notification service
    slack_notification_service_mock = mocker.patch.object(slack_notification_service, "notify")

    # WHEN calling handle
    # THEN a CG error should be raised
    with pytest.raises(CgError):
        external_sample_transferred_handler.handle(config=config, event_payload=event_payload)

    # THEN a Slack notification should have been sent out to prodbioinfo
    calls = slack_notification_service_mock.call_args_list
    first_call = calls[0]
    assert first_call.kwargs["recipient"] == "http.bingus.gov"
    assert first_call.kwargs["notification"].title == "Failed to store an external sample"
    assert (
        first_call.kwargs["notification"].message
        == f"{EXTERNAL_SAMPLE_TRANSFERRED_EVENT} failed for sample ACC123"
    )
    assert "No sequencing files" in first_call.kwargs["notification"].error_text


def test_storing_succeeds_deletion_fails(mocker: MockerFixture):
    # GIVEN a StatusDB
    status_db: TypedMock[Store] = create_typed_mock(Store)
    sample: Sample = create_autospec(Sample, customer_id=1)
    sample.name = "sample-name"
    status_db.as_type.get_sample_by_internal_id_strict = Mock(return_value=sample)

    # GIVEN a HousekeeperAPI
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    version = create_autospec(Version)
    bundle = create_autospec(Bundle, versions=[version])
    housekeeper_api.as_type.add_new_bundle_and_version = Mock(return_value=bundle)

    # GIVEN a NATS configuration
    nats_config: NatsConfig = create_autospec(NatsConfig, stream="cg-test")

    # GIVEN a CG config
    config: CGConfig = create_autospec(
        CGConfig,
        status_db=status_db.as_type,
        housekeeper_api=housekeeper_api.as_type,
        nats=nats_config,
    )

    # GIVEN a publisher for completion events
    publish_mock = mocker.patch.object(
        external_sample_transferred_handler.event_publisher, "publish_event"
    )

    # GIVEN a valid event payload
    event_payload = {
        SAMPLE_INTERNAL_ID_FIELD: "ACC123",
        "cluster_location": "/path/to/mirrored/sample",
        "transfer_completed_at": "2026-08-31T14:41:00",
    }

    # GIVEN that two files have been transferred for the given sample
    path_r1 = Path("file_R1.fastq.gz")
    path_r2 = Path("file_R2.fastq.gz")
    mocker.patch.object(Path, "glob", return_value=[path_r1, path_r2])

    # GIVEN that deleting the directory goes poorly
    rmtree_mock = mocker.patch.object(shutil, "rmtree", side_effect=Exception("CATASTROPHE"))

    notify_mock = mocker.patch.object(slack_notification_service, "notify")

    # WHEN calling handle
    external_sample_transferred_handler.handle(config=config, event_payload=event_payload)

    # THEN the external sample transferred_at was set
    expected_datetime = datetime(year=2026, month=8, day=31, hour=14, minute=41)
    status_db.as_mock.update_external_sample.assert_called_once_with(
        sample_name="sample-name", customer_id=1, transferred_at=expected_datetime
    )

    # THEN a housekeeper bundle and version was created for the sample
    housekeeper_api.as_mock.add_new_bundle_and_version.assert_called_once_with("ACC123")

    # THEN all sequencing files were added to the bundle
    r1_call = call(path=str(path_r1.absolute()), version_obj=version, tags=["ACC123", "fastq"])
    r2_call = call(path=str(path_r2.absolute()), version_obj=version, tags=["ACC123", "fastq"])
    function_calls: list = housekeeper_api.as_mock.add_file.call_args_list
    assert r1_call in function_calls
    assert r2_call in function_calls
    assert len(function_calls) == 2

    # THEN the changes were commited so that we can be certain that they are there when the next
    # event is received
    status_db.as_mock.commit_to_store.assert_called_once()

    # THEN an event was published saying the sample was stored
    publish_mock.assert_called_once_with(
        nats_config=nats_config,
        event_name=EXTERNAL_SAMPLE_STORED_EVENT,
        event_payload={SAMPLE_INTERNAL_ID_FIELD: "ACC123"},
    )

    # THEN a notification should have been sent to the sysdev team about the failure to delete the directory
    calls = notify_mock.call_args_list
    first_call = calls[0]
    assert first_call.kwargs["recipient"] == "bongus"
    assert (
        first_call.kwargs["notification"].title
        == f"Failed to delete {event_payload['cluster_location']}"
    )
    assert (
        first_call.kwargs["notification"].message
        == f"{EXTERNAL_SAMPLE_TRANSFERRED_EVENT} succeeded for sample ACC123 but failed to delete mirrored directory at {event_payload['cluster_location']}"
    )
    assert "CATASTROPHE" in first_call.kwargs["notification"].error_text
