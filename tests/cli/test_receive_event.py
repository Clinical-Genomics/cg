from json import JSONDecodeError
from unittest.mock import create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.receive_event import event_dispatching, receive_event
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_receive_event_success(mocker: MockerFixture):
    # GIVEN a CliRunner
    cli_runner = CliRunner()

    dispatch_spy = mocker.spy(event_dispatching, "dispatch")

    # GIVEN a CGConfig
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN that the event has metadata
    metadata = '{"sequence": {"consumer": 2, "stream": 1}, "num_pending": 0, "num_delivered": 2, "timestamp": "2026-09-29T11:32:12", "stream": "cg-local-dev", "consumer": "cluster-consumer"}'

    # WHEN calling the receive event command
    result = cli_runner.invoke(
        receive_event,
        args=[
            "something-happened",
            "--event-payload",
            '{"key": "value"}',
            "--event-metadata",
            metadata,
        ],
        obj=cg_config,
    )

    # THEN the result exits successfully
    assert result.exit_code == 0

    # THEN it calls the dispatch function
    dispatch_spy.assert_called_once_with(
        config=cg_config,
        event_name="something-happened",
        event_payload={"key": "value"},
        event_metadata={
            "sequence": {"consumer": 2, "stream": 1},
            "num_pending": 0,
            "num_delivered": 2,
            "timestamp": "2026-09-29T11:32:12",
            "stream": "cg-local-dev",
            "consumer": "cluster-consumer",
        },
    )

    # THEN the database changes should have been committed
    status_db.as_mock.commit_to_store.assert_called_once_with()

    # THEN
    # TODO


def test_receive_event_json_parsing_fails(mocker: MockerFixture):
    # GIVEN a CliRunner
    cli_runner = CliRunner()

    dispatch_spy = mocker.spy(event_dispatching, "dispatch")

    # GIVEN a CGConfig
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(CGConfig, status_db=status_db.as_type)

    # WHEN calling the receive event command with a malformed json
    result = cli_runner.invoke(
        receive_event,
        args=[
            "something-happened",
            "--event-payload",
            "this is a string",
            "--event-metadata",
            "{}",
        ],
        obj=cg_config,
    )

    # THEN it should not call the dispatch function
    dispatch_spy.assert_not_called()

    # THEN the result exits unsuccessfully
    assert result.exit_code != 0

    # THEN the error is because of the malformed json input
    assert isinstance(result.exception, JSONDecodeError)

    # THEN the database changes should NOT have been committed
    status_db.as_mock.commit_to_store.assert_not_called()


@pytest.mark.parametrize(
    "additional_args",
    [
        [],
        ["--event-payload", ""],
        ["--event-payload", '{"key": "value"}'],
        ["--event-payload", '{"key": "value"}', "--event-metadata", ""],
    ],
    ids=[
        "no event payload nor metadata arguments",
        "empty event payload argument",
        "no metadata argument",
        "empty metadata argument",
    ],
)
def test_receive_event_no_payload(mocker: MockerFixture, additional_args: list[str]):
    # GIVEN the cli runner
    cli_runner = CliRunner()

    # GIVEN a CGConfig with a store
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    dispatch_spy = mocker.spy(event_dispatching, "dispatch")

    # WHEN calling the receive event command with no payload
    result = cli_runner.invoke(
        receive_event,
        args=["something-happened"] + additional_args,
        obj=cg_config,
    )

    # THEN the result exits successfully
    assert result.exit_code == 0

    # THEN it should not call the dispatch function
    dispatch_spy.assert_not_called()

    # THEN the database changes should NOT have been committed
    status_db.as_mock.commit_to_store.assert_not_called()


def test_receive_event_dispatch_raises(mocker: MockerFixture):
    # GIVEN the cli runner
    cli_runner = CliRunner()

    # GIVEN some JSON-formatted payload
    event_payload = "{}"

    # GIVEN a CG config
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN that dispatch function raises an error
    mocker.patch.object(event_dispatching, "dispatch", side_effect=Exception)

    # WHEN calling the receive event command
    result = cli_runner.invoke(
        receive_event,
        args=["something-happened", "--event-payload", event_payload, "--event-metadata", "{}"],
        obj=cg_config,
    )

    # THEN the exit code should be non-zero
    assert result.exit_code != 0

    # THEN the database changes should NOT have been committed
    status_db.as_mock.commit_to_store.assert_not_called()
