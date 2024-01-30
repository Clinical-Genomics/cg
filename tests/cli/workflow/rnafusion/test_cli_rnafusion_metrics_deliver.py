"""Tests for the metrics-deliver cli command."""

import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import metrics_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


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
    rnafusion_mock_analysis_finish,
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
