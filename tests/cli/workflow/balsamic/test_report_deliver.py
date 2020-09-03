"""Tests for the report-deliver cli command"""

import logging
from pathlib import Path

from cg.cli.workflow.balsamic.base import report_deliver

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context: dict):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(report_deliver, obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context: dict, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    # WHEN running
    result = cli_runner.invoke(report_deliver, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "not found" in caplog.text


def test_without_samples(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "0" in caplog.text


def test_without_config(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_case_without_analysis_finish(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and config file but no analysis_finish"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no analysis_finish is found
    assert "deliverables file will not be created" in caplog.text


def test_dry_run(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and analysis_finish which should execute successfully"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config and analysis_finish exist where they should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_analysis_finish_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_analysis_finish_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN balsamic and case_id should be found in command string
    assert "balsamic" in caplog.text
    assert case_id + ".json" in caplog.text


def test_qc_option(cli_runner, balsamic_context: dict, caplog):
    """Test command with case_id and qc option + config and analysis_finish
    which should execute successfully"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    option_key = "--analysis-type"
    option_value = "qc"
    # WHEN ensuring case config and analysis_finish exist where they should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).touch(exist_ok=True)
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_analysis_finish_path(case_id)).parent,
        exist_ok=True,
    )
    Path(balsamic_context["BalsamicAnalysisAPI"].get_analysis_finish_path(case_id)).touch(
        exist_ok=True
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        report_deliver, [case_id, "--dry-run", option_key, option_value], obj=balsamic_context
    )
    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN balsamic, case_id, and qc options should be found in command string
    assert "balsamic" in caplog.text
    assert case_id + ".json" in caplog.text
    assert option_key in caplog.text
    assert option_value in caplog.text
