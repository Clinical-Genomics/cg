"""This script tests the cli methods to run balsamic"""
import subprocess
import logging
from unittest import mock

from cg.cli.workflow.balsamic.base import run

EXIT_SUCCESS = 0


def test_without_options(cli_runner):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_case(cli_runner, balsamic_context, caplog, balsamic_dummy_case):
    """Test command with case to start with"""

    # GIVEN case-id, and malconfigured pipeline
    case_id = balsamic_dummy_case

    dummy_stdout = "dummy_stdout"
    dummy_stderr = "dummy_stderr"
    dummy_returncode_success = 0

    caplog.set_level(logging.INFO)

    context = balsamic_context
    
    # WHEN running balsamic on "case"
    with mock.patch.object(subprocess, "run") as mocked:
        mocked.return_value.stdout = dummy_stdout.encode("utf-8")
        mocked.return_value.stderr = dummy_stderr.encode("utf-8")
        mocked.return_value.returncode = dummy_returncode_success
        result = cli_runner.invoke(run, [case_id], obj=context)

        # THEN assert that command is in log output
        assert " ".join(["balsamic", "run", "analysis"]) in caplog.text


def test_dry(cli_runner, balsamic_context, caplog, balsamic_dummy_case):
    """Test command with dry option"""

    # GIVEN case-id
    case_id = balsamic_dummy_case

    caplog.set_level(logging.INFO)

    context = balsamic_context

    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=context)

    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


def test_run_analysis(cli_runner, balsamic_context, caplog, balsamic_dummy_case):
    """Test command with run-analysis option"""

    # GIVEN case-id
    case_id = balsamic_dummy_case

    caplog.set_level(logging.INFO)

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", "--run-analysis"], obj=context)

    # THEN dry-print should include the option
    assert result.exit_code == EXIT_SUCCESS
    assert "--run-analysis" in caplog.text


def test_config(cli_runner, balsamic_context, caplog, balsamic_dummy_case):
    """Test command with config option"""

    # GIVEN case-id
    case_id = balsamic_dummy_case
    option_key = "--config"
    option_value = "config-path"

    caplog.set_level(logging.INFO)
    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=context)

    # THEN dry-print should include the the option-value but not the case-id
    assert result.exit_code == EXIT_SUCCESS
    assert option_value in caplog.text
    assert case_id not in caplog.text


def test_email(cli_runner, balsamic_context, caplog, balsamic_dummy_case):
    """Test command with config option"""

    # GIVEN case-id
    case_id = balsamic_dummy_case
    option_key = "--email"
    option_value = "salmon.moose@test.com"

    caplog.set_level(logging.INFO)

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=context)

    # THEN dry-print should include the the option-value but not the case-id
    assert result.exit_code == EXIT_SUCCESS
    assert "--mail-user" in caplog.text
    assert option_value in caplog.text


def test_priority(cli_runner, balsamic_context, caplog, balsamic_dummy_case):
    """Test command with priority option"""

    # GIVEN case-id
    case_id = balsamic_dummy_case
    option_key = "--priority"
    option_value = "high"

    caplog.set_level(logging.INFO)

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=context)

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    assert "--qos" in caplog.text
    assert option_value in caplog.text
