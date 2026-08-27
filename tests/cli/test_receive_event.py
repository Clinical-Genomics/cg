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

    # WHEN calling the receive event command
    result = cli_runner.invoke(
        receive_event,
        args=["something-happened", "--event-payload", '{"key": "value"}'],
        obj=cg_config,
    )

    # THEN it calls the dispatch function
    dispatch_spy.assert_called_once_with(
        config=cg_config, event_name="something-happened", event_payload={"key": "value"}
    )

    # THEN the result exits successfully
    assert result.exit_code == 0

    # THEN the database changes should have been committed
    status_db.as_mock.commit_to_store.assert_called_once_with()


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
        args=["something-happened", "--event-payload", "this is a string"],
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
    ],
    ids=["no_data_argument", "empty_data_argument"],
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

    # THEN it should not call the dispatch function
    dispatch_spy.assert_not_called()

    # THEN the result exits successfully
    assert result.exit_code == 0

    # THEN the database changes should NOT have been committed
    status_db.as_mock.commit_to_store.assert_not_called()


def test_receive_event_dispatch_raises(mocker: MockerFixture):
    # GIVEN the cli runner
    cli_runner = CliRunner()

    # GIVEN some JSON-formatted data
    data = "{}"

    # GIVEN a CG config
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN that dispatch function raises an error
    mocker.patch.object(event_dispatching, "dispatch", side_effect=Exception)

    # WHEN calling the receive event command
    result = cli_runner.invoke(
        receive_event,
        args=["something-happened", "--data", data],
        obj=cg_config,
    )

    # THEN the exit code should be non-zero
    assert result.exit_code != 0

    # THEN the database changes should NOT have been committed
    status_db.as_mock.commit_to_store.assert_not_called()
