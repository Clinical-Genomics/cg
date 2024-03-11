"""This script tests the run cli command"""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.raredisease.base import run
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_with_revision(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    raredisease_case_id: str,
    mock_config,
):
    """Test command with case_id and config file using tower and specifying a revision."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = raredisease_case_id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--from-start", "--revision", "2.1.0"], obj=raredisease_context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower
    assert "--revision 2.1.0" in caplog.text


def test_resume_with_id(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    raredisease_case_id: str,
    mock_config,
    tower_id,
):
    """Test resume command given a NF-Tower run ID using Tower."""
    caplog.set_level(logging.INFO)

    # GIVEN a case-id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        run, [raredisease_case_id, "--nf-tower-id", tower_id, "--dry-run"], obj=raredisease_context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower for relaunch
    assert "Workflow will be resumed from run" in caplog.text
    assert "tw runs relaunch" in caplog.text


def test_resume_without_id_error(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    raredisease_case_id: str,
    mock_config,
):
    """Test resume command without providing NF-Tower ID and without existing Trailblazer Tower config file."""
    caplog.set_level(logging.INFO)

    # GIVEN case-id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    cli_runner.invoke(run, [raredisease_case_id, "--dry-run"], obj=raredisease_context)

    # THEN command should raise error
    assert "Could not resume analysis: No NF-Tower ID found for case" in caplog.text
    pytest.raises(FileNotFoundError)
