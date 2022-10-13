"""Tests for the report-deliver cli command"""

import logging
from pathlib import Path

from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import report_deliver
from cg.models.cg_config import CGConfig
from cg.constants import EXIT_SUCCESS


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(report_deliver, obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.WARNING)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not rnafusion_context.status_db.family(case_id)
    # WHEN running
    result = cli_runner.invoke(report_deliver, [case_id], obj=rnafusion_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "could not be found" in caplog.text


def test_without_samples(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"

    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no samples exist in case
    assert "no samples" in caplog.text


def test_dry_run(cli_runner: CliRunner, rnafusion_context: CGConfig, mock_analysis_finish, caplog):
    """Test command with case_id and analysis_finish which should execute successfully"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "rnafusion_case_enough_reads"
    # WHEN ensuring case config and analysis_finish exist where they should be stored
    Path.mkdir(
        Path(rnafusion_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(rnafusion_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=rnafusion_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN rnafusion and case_id should be found in command string
    assert "rnafusion" in caplog.text
    assert case_id in caplog.text
