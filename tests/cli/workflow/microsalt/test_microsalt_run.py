""" This file groups all tests related to microsalt start creation """
import logging

from cg.cli.workflow.microsalt.base import run
from cg.models.cg_config import CGConfig
from click.testing import CliRunner

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner: CliRunner, base_context: CGConfig):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS


def test_dry_arguments(cli_runner: CliRunner, base_context: CGConfig, ticket_id, caplog):
    """Test command dry"""

    # GIVEN
    caplog.set_level(logging.INFO)

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, [ticket_id, "-t", "-d"], obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code == EXIT_SUCCESS
    assert f"Running command" in caplog.text
