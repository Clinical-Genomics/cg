"""Tests for the metrics-deliver cli command."""

import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import metrics_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case_id

    # WHEN dry running without anything specified
    result = cli_runner.invoke(metrics_deliver, obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.WARNING)

    # GIVEN case_id not in database
    assert not rnafusion_context.status_db.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )

    # WHEN running
    result = cli_runner.invoke(metrics_deliver, [case_id_does_not_exist], obj=rnafusion_context)

    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


def test_without_samples(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
):
    """Test command with case_id and no samples."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        metrics_deliver, [no_sample_case_id, "--dry-run"], obj=rnafusion_context
    )

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no samples exist in case
    assert "no samples" in caplog.text


def test_metrics_deliver(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with case_id and analysis_finish which should execute successfully."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id

    # WHEN dry running with dry specified
    result = cli_runner.invoke(metrics_deliver, [rnafusion_case_id], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN rnafusion and case_id should be found in command string
    assert "Writing metrics deliverables file to" in caplog.text
