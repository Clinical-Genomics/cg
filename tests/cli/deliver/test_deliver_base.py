"""Tests for the deliver base command"""

from click.testing import CliRunner
from cg.cli.base import base as base_command
from cg.cli.deliver.base import deliver as deliver_cmd
from cg.store import Store
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


def test_run_deliver_analysis_help(hk_config_dict: dict):
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner
    runner = CliRunner()
    # GIVEN a context with store and housekeeper information
    hk_config_dict["database"] = "sqlite:///:memory:"

    # WHEN running cg deliver help
    result = runner.invoke(deliver_cmd, ["analysis", "--help"], obj=hk_config_dict)

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "Deliver analysis files to customer inbox" in result.output
