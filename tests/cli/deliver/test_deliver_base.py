"""Tests for the deliver base command"""

from cg.cli.deliver.base import deliver as deliver_cmd
from cg.cli.deliver.base import rsync as rsync_cmd
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_run_base_help():
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN running cg deliver help
    result = runner.invoke(deliver_cmd, ["--help"])

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "Deliver files with CG" in result.output


def test_run_deliver_analysis_help(base_context: CGConfig):
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner
    runner = CliRunner()
    # GIVEN a context with store and housekeeper information

    # WHEN running cg deliver help
    result = runner.invoke(deliver_cmd, ["analysis", "--help"], obj=base_context)

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "Deliver analysis files to customer inbox" in result.output
