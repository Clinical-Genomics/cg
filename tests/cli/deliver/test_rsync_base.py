"""Tests for rsync base"""

import logging

from cg.cli.deliver.base import rsync
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_rsync_help(cli_runner):
    """Test to run the rsync function"""
    # GIVEN a cli runner

    # WHEN running cg deliver rsync
    result = cli_runner.invoke(rsync, ["--dry-run", "--help"])

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "The folder generated using the" in result.output


def test_run_rsync_command_no_case(cg_context: CGConfig, cli_runner, helpers, caplog):
    """Test generating the rsync command for ticket that doesnt exist"""
    caplog.set_level(logging.INFO)

    # Given an invalid ticket id where case was not created

    # WHEN running deliver rsync command
    result = cli_runner.invoke(rsync, ["--dry-run", "9898989898"], obj=cg_context)

    # THEN command failed successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN process generates error message that case cant be found
    assert "Could not find any cases for ticket" in caplog.text
