"""Tests for the report-deliver cli command"""

import logging
from pathlib import Path

from click.testing import CliRunner

from cg.cli.workflow.balsamic.base import report_deliver
from cg.models.cg_config import CGConfig

EXIT_SUCCESS = 0
NO_CONFIG_FOUND = "No config file found"


def test_without_options(cli_runner: CliRunner, balsamic_context: CGConfig):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(report_deliver, obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.WARNING)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id)
    # WHEN running
    result = cli_runner.invoke(report_deliver, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "could not be found" in caplog.text


def test_without_samples(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"

    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no samples exist in case
    assert "no samples" in caplog.text


def test_without_config(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert NO_CONFIG_FOUND in caplog.text


def test_dry_run(cli_runner: CliRunner, balsamic_context: CGConfig, caplog):
    """Test command with case_id and analysis_finish which should execute successfully"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config and analysis_finish exist where they should be stored
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN balsamic and case_id should be found in command string
    assert "balsamic" in caplog.text
    assert case_id + ".json" in caplog.text
