from unittest.mock import ANY, create_autospec

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
        args=["cg-test.something-happened", "--data", "{'key': 'value'}"],
        obj=cg_config,
        catch_exceptions=False,
    )

    # THEN it calls the event handler
    handle_spy.assert_called_once_with(
        config=cg_config, event_name="cg-test.something-happened", data=ANY
    )

    # THEN the result exits successfully
    assert result.exit_code == 0


def test_receive_event_json_parsing_fails():
    pass
