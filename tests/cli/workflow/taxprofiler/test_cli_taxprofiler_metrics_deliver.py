"""Tests for the metrics-deliver cli command."""

import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import metrics_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case_id

    # WHEN dry running without anything specified
    result = cli_runner.invoke(metrics_deliver, obj=taxprofiler_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
):
    """Test metrics-deliver command with invalid case."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    assert not taxprofiler_context.status_db.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )
    # WHEN running
    result = cli_runner.invoke(metrics_deliver, [case_id_does_not_exist], obj=taxprofiler_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert f"{case_id_does_not_exist} could not be found" in caplog.text
