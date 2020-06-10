"""This script tests the cli methods to create the case config for balsamic"""

from cg.cli.workflow.balsamic.store import generate_deliverables_file
from cg.exc import CgError

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_store_context):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(generate_deliverables_file, obj=balsamic_store_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_dry_with_config_file(cli_runner, balsamic_store_context, balsamic_case, config_file):
    """Test command with --dry option"""

    # GIVEN case-id
    case_id = balsamic_case.internal_id

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        generate_deliverables_file,
        [case_id, "--dry-run", "-c", config_file],
        obj=balsamic_store_context,
    )

    # THEN command should print the balsamic command-string to generate the deliverables fils
    assert "report deliver" in result.output
    assert result.exit_code == EXIT_SUCCESS


def test_without_config_file(cli_runner, balsamic_store_context, balsamic_case):
    """Test command to generate deliverables file without supplying the config"""

    # GIVEN a case

    # WHEN calling generate deliverables file but the config is missing on disk
    result = cli_runner.invoke(
        generate_deliverables_file,
        [balsamic_case.internal_id, "--dry-run"],
        obj=balsamic_store_context,
    )

    # THEN the result of the call should be a non SUCCESS
    assert isinstance(result.exception, FileNotFoundError)
    assert result.exit_code != EXIT_SUCCESS


def test_with_missing_case(cli_runner, balsamic_store_context):
    """Test command with case to start with"""

    # GIVEN case-id not in database
    case_id = "soberelephant"

    # WHEN running
    result = cli_runner.invoke(
        generate_deliverables_file, [case_id, "--dry-run"], obj=balsamic_store_context
    )

    # THEN the command should fail and mention the case id in the fail message
    assert isinstance(result.exception, CgError)
    assert f"Case {case_id} not found" in result.exception.message
    assert result.exit_code != EXIT_SUCCESS
