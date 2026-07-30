from typing import cast

import pytest
import rich_click as click
from click.testing import CliRunner, Result

from cg.cli.listen import listen
from cg.server.app_config import AppConfig


# TODO: fix this test when implementation is complete
@pytest.mark.xfail(reason="Standalone listen command is not fully implemented yet")
def test_standalone_listen_uses_app_config():
    # WHEN invoking the standalone listen command
    runner = CliRunner()
    listen_command = cast(click.Command, listen)
    result: Result = runner.invoke(listen_command)
    help_result: Result = runner.invoke(listen_command, ["--help"])

    # THEN the command exits successfully and keeps an AppConfig-only callback signature
    assert result.exit_code == 0
    assert listen.callback.__annotations__["app_config"] is AppConfig
    assert help_result.exit_code == 0
    assert "--config" not in help_result.output
