"""This script tests the cli methods to create the case config for balsamic"""
import logging
from pathlib import Path

import pytest
from cg.cli.workflow.balsamic.store import generate_deliverables_file

EXIT_SUCCESS = 0


def test_without_options(cli_runner, balsamic_context):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(generate_deliverables_file, obj=balsamic_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_dry(cli_runner, balsamic_context, balsamic_case):
    """Test command with --dry option"""

    # GIVEN case-id
    case_id = balsamic_case.internal_id

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        generate_deliverables_file, [case_id, "--dry-run"], obj=balsamic_context
    )

    # THEN command should print the balsamic command-string to generate the deliverables fils
    assert result.exit_code == EXIT_SUCCESS
    assert "plugins deliver" in result.output
    assert case_id in result.output


def test_without_file(cli_runner, balsamic_context, balsamic_case):
    """Test command to generate deliverables file without supplying the config"""

    # GIVEN no meta file for a balsamic analysis

    # WHEN calling generate deliverables file
    result = cli_runner.invoke(
        generate_deliverables_file, [balsamic_case.internal_id, "--dry-run"], obj=balsamic_context
    )

    # THEN we should get a message that the deliverables file was created
    assert result.exit_code == EXIT_SUCCESS
    assert "plugins deliver" in result.output
    assert "--sample-config" in result.output
    assert ".json" in result.output


def test_with_missing_case(cli_runner, balsamic_context, caplog):
    """Test command with case to start with"""

    # GIVEN case-id not in database
    case_id = "soberelephant"

    # WHEN running
    result = cli_runner.invoke(
        generate_deliverables_file, [case_id, "--dry-run"], obj=balsamic_context
    )

    # THEN the command should fail and mention the case id in the fail message
    assert result.exit_code == EXIT_SUCCESS

    assert f"Case {case_id} not found" in result.output
