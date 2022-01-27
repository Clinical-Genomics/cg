"""This script tests the cli method to clean old balsamic fastqs"""

from click.testing import CliRunner

from cg.cli.clean.base import balsamic_fastqs
from cg.models.cg_config import CGConfig

EXIT_SUCCESS = 0


def test_balsamic_fastqs_without_options(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN

    # WHEN running without anything specified
    result = cli_runner.invoke(balsamic_fastqs, obj=clean_context)

    # THEN command run happily
    assert result.exit_code == EXIT_SUCCESS
    assert "Missing argument" not in result.output


def test_balsamic_fastqs_with_dry_run(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN

    # WHEN running with dry-run specified
    result = cli_runner.invoke(balsamic_fastqs, ["--dry-run"], obj=clean_context)

    # THEN command should run happily
    assert result.exit_code == EXIT_SUCCESS


def test_balsamic_fastqs_with_no_confirm(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN

    # WHEN running with dry-run specified
    result = cli_runner.invoke(balsamic_fastqs, ["--yes"], obj=clean_context)

    # THEN command should run happily
    assert result.exit_code == EXIT_SUCCESS


def test_balsamic_fastqs_with_days_old(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN

    # WHEN running with dry-run specified
    older_than = 30
    result = cli_runner.invoke(balsamic_fastqs, ["--older-than", older_than], obj=clean_context)

    # THEN command should run happily
    assert result.exit_code == EXIT_SUCCESS


def test_balsamic_fastqs_with_no_older_than(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN

    # WHEN running with dry-run specified
    newer_than = 30
    result = cli_runner.invoke(balsamic_fastqs, ["--newer-than", newer_than], obj=clean_context)

    # THEN command should run happily
    assert result.exit_code == EXIT_SUCCESS
