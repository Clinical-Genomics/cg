"""Tests for the deliver base command"""

import logging

from click.testing import CliRunner

from cg.cli.deliver.base import deliver as deliver_cmd
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_run_base_help(cli_runner: CliRunner):
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner

    # WHEN running cg deliver help
    result = cli_runner.invoke(deliver_cmd, ["--help"])

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS
    # THEN assert the information is printed
    assert "Deliver files with CG" in result.output


def test_run_deliver_analysis_help(cli_runner: CliRunner, base_context: CGConfig):
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner
    # GIVEN a context with store and housekeeper information

    # WHEN running cg deliver help
    result = cli_runner.invoke(deliver_cmd, ["case", "--help"], obj=base_context)

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS


def test_run_deliver_ticket_help(cli_runner: CliRunner, base_context: CGConfig):
    """Test to run the deliver base command with --help"""
    # GIVEN a cli runner
    # GIVEN a context with store and housekeeper information

    # WHEN running cg deliver help
    result = cli_runner.invoke(deliver_cmd, ["ticket", "--help"], obj=base_context)

    # THEN assert the command exists without problems
    assert result.exit_code == EXIT_SUCCESS


def test_run_deliver_ticket(cli_runner: CliRunner, cg_context: CGConfig, ticket_id):
    """Test for delivering tu customer inbox"""
    # GIVEN a cli runner

    # WHEN running cg deliver ticket
    result = cli_runner.invoke(
        deliver_cmd,
        ["ticket", "--dry-run", "--ticket", ticket_id],
        obj=cg_context,
    )

    # THEN assert that files are delivered
    assert result.exit_code == EXIT_SUCCESS
