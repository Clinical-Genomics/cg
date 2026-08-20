from json import JSONDecodeError
from unittest.mock import create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.receive_event import event_handler, receive_event
from cg.models.cg_config import CGConfig


def test_receive_event_success(mocker: MockerFixture):
    # GIVEN a CliRunner
    cli_runner = CliRunner()

    handle_spy = mocker.spy(event_handler, "handle")

    # GIVEN a CGConfig
    cg_config = create_autospec(CGConfig)

    # WHEN calling the receive event command
    result = cli_runner.invoke(
        receive_event,
        args=["cg-test.something-happened", "--data", '{"key": "value"}'],
        obj=cg_config,
    )

    # THEN it calls the event handler
    handle_spy.assert_called_once_with(
        config=cg_config, event_name="cg-test.something-happened", data={"key": "value"}
    )

    # THEN the result exits successfully
    assert result.exit_code == 0


def test_receive_event_json_parsing_fails(mocker: MockerFixture):
    # GIVEN a CliRunner
    cli_runner = CliRunner()

    handle_spy = mocker.spy(event_handler, "handle")

    # GIVEN a CGConfig
    cg_config = create_autospec(CGConfig)

    # WHEN calling the receive event command with a malformed json
    result = cli_runner.invoke(
        receive_event,
        args=["cg-test.something-happened", "--data", "this is a string"],
        obj=cg_config,
    )

    # THEN it should not call the event handler
    handle_spy.assert_not_called()

    # THEN the result exits unsuccessfully
    assert result.exit_code != 0

    # THEN the error is because of the malformed json input
    assert isinstance(result.exception, JSONDecodeError)


def test_receive_event_no_data_flag(mocker: MockerFixture):
    # GIVEN the cli runner
    cli_runner = CliRunner()

    handle_spy = mocker.spy(event_handler, "handle")
    # WHEN calling the receive event command with no data
    result = cli_runner.invoke(
        receive_event,
        args=["cg-test.something-happened"],
        obj=create_autospec(CGConfig),
    )

    handle_spy.assert_not_called()

    # THEN the result exits successfully
    assert result.exit_code == 0


def test_receive_event_no_data(mocker: MockerFixture):
    # GIVEN the cli runner
    cli_runner = CliRunner()

    handle_spy = mocker.spy(event_handler, "handle")
    # WHEN calling the receive event command with no data
    result = cli_runner.invoke(
        receive_event,
        args=["cg-test.something-happened", "--data", ""],
        obj=create_autospec(CGConfig),
    )

    handle_spy.assert_not_called()

    # THEN the result exits successfully
    assert result.exit_code == 0
