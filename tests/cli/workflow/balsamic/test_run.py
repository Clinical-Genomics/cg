"""This script tests the cli methods to run balsamic"""
import subprocess
import logging
from unittest import mock

from cg.cli.workflow.balsamic.base import run

EXIT_SUCCESS = 0


def test_without_options(cli_runner):
    """Test command with dry option"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_dry(cli_runner, balsamic_context, caplog):
    """Test command with dry option"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


def test_run_analysis(cli_runner, balsamic_context, caplog):
    """Test command with run-analysis option"""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", "--run-analysis"], obj=balsamic_context)
    # THEN dry-print should include the option
    assert result.exit_code == EXIT_SUCCESS
    assert "--run-analysis" in caplog.text


def test_priority(cli_runner, balsamic_context, caplog):
    """Test command with priority option"""
    caplog.set_level(logging.INFO)
    # GIVEN valid case-id
    case_id = "balsamic_case_wgs_single"
    option_key = "--priority"
    option_value = "high"
    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=balsamic_context)
    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    assert "--qos" in caplog.text
    assert option_value in caplog.text
