"""This script tests the cli methods to run balsamic"""

from cg.cli.balsamic import run

EXIT_SUCCESS = 0


def test_without_options(cli_runner):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_case(cli_runner, base_context):
    """Test command with case to start with"""

    # GIVEN case-id, and malconfigured pipeline
    case_id = "soberelephant"

    context = base_context

    # WHEN running
    result = cli_runner.invoke(run, [case_id], obj=context)

    # THEN command should successfully call the comamnd it creates
    assert result.exit_code == EXIT_SUCCESS


def test_dry(cli_runner, base_context):
    """Test command with dry option"""

    # GIVEN case-id
    case_id = "sillyshark"

    context = base_context

    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=context)

    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert case_id in result.output


def test_run_analysis(cli_runner, base_context):
    """Test command with run-analysis option"""

    # GIVEN case-id
    case_id = "slimwhale"

    context = base_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--run-analysis"], obj=context
    )

    # THEN dry-print should include the option
    assert result.exit_code == EXIT_SUCCESS
    assert "--run-analysis" in result.output


def test_config(cli_runner, base_context):
    """Test command with config option"""

    # GIVEN case-id
    case_id = "analogeel"
    option_key = "--config"
    option_value = "config-path"

    context = base_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", option_key, option_value], obj=context
    )

    # THEN dry-print should include the the option-value but not the case-id
    assert result.exit_code == EXIT_SUCCESS
    assert option_value in result.output
    assert case_id not in result.output


def test_email(cli_runner, base_context):
    """Test command with config option"""

    # GIVEN case-id
    case_id = "mightymonkey"
    option_key = "--email"
    option_value = "salmon.moose@test.com"

    context = base_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", option_key, option_value], obj=context
    )

    # THEN dry-print should include the the option-value but not the case-id
    assert result.exit_code == EXIT_SUCCESS
    assert "--mail-user" in result.output
    assert option_value in result.output


def test_priority(cli_runner, base_context):
    """Test command with priority option"""

    # GIVEN case-id
    case_id = "weakgorilla"
    option_key = "--priority"
    option_value = "high"

    context = base_context

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", option_key, option_value], obj=context
    )

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    assert "--qos" in result.output
    assert option_value in result.output
