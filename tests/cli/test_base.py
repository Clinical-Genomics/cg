from click.testing import CliRunner, Result

import cg
from cg.cli.base import base


def test_cli_version(cli_runner: CliRunner):
    # GIVEN I want to see the version of the program
    # WHEN asking to see the version
    result: Result = cli_runner.invoke(base, ["--version"])
    # THEN it should display the version of the program
    # THEN it should print the name and version of the tool only
    assert cg.__title__ in result.output
    assert cg.__version__ in result.output


def test_list_commands(cli_runner: CliRunner):
    # WHEN using simplest command 'cg'
    result = cli_runner.invoke(base, [])
    # THEN it should just work ;-)
    assert result.exit_code == 0


def test_missing_command(cli_runner: CliRunner):
    # WHEN invoking a missing command
    result = cli_runner.invoke(base, ["i_dont_exist"])
    # THEN context should abort
    assert result.exit_code != 0
