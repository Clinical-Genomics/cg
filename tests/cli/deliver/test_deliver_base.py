"""Tests for the deliver base command"""

from click.testing import CliRunner
from cg.cli.base import base as base_command

from cg.constants import EXIT_SUCCESS


def test_run_base_help():
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running cg deliver help
    result = runner.invoke(base_command, ["deliver", "--help"])

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "Deliver files with CG" in result.output
