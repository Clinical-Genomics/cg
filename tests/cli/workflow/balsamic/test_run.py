"""This script tests the cli methods to run balsamic"""
import logging

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


def test_with_case(cli_runner, balsamic_context):
    """Test command with case to start with"""

    # GIVEN case-id, and malconfigured pipeline
    case_id = "soberelephant"

    context = balsamic_context

    # WHEN running
    result = cli_runner.invoke(run, [case_id], obj=context)

    # THEN command should successfully call the command it creates
    assert result.exit_code == EXIT_SUCCESS


def test_dry(cli_runner, balsamic_context, caplog):
    """Test command with dry option"""

    # GIVEN case-id
    case_id = "sillyshark"

    context = balsamic_context

    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=context)

    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "balsamic" in caplog.text
        assert case_id in caplog.text


def test_run_analysis(cli_runner, balsamic_context, caplog):
    """Test command with run-analysis option"""

    # GIVEN case-id
    case_id = "slimwhale"

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", "--run-analysis"], obj=context)

    # THEN dry-print should include the option
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "--run-analysis" in caplog.text


def test_config(cli_runner, balsamic_context, caplog):
    """Test command with config option"""

    # GIVEN case-id
    case_id = "analogeel"
    option_key = "--config"
    option_value = "config-path"

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=context)

    # THEN dry-print should include the the option-value but not the case-id
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert option_value in caplog.text
        assert case_id not in caplog.text


def test_email(cli_runner, balsamic_context, caplog):
    """Test command with config option"""

    # GIVEN case-id
    case_id = "mightymonkey"
    option_key = "--email"
    option_value = "salmon.moose@test.com"

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=context)

    # THEN dry-print should include the the option-value but not the case-id
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "--mail-user" in caplog.text
        assert option_value in caplog.text


def test_priority(cli_runner, balsamic_context, caplog):
    """Test command with priority option"""

    # GIVEN case-id
    case_id = "weakgorilla"
    option_key = "--priority"
    option_value = "high"

    context = balsamic_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", option_key, option_value], obj=context)

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "--qos" in caplog.text
        assert option_value in caplog.text
