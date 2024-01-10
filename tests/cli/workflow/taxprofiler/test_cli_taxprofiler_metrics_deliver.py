"""Tests for the metrics-deliver CLI command."""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import metrics_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.io.yaml import read_yaml


def test_without_options(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test command without 'case_id' argument."""
    # GIVEN no case id

    # WHEN using dry run without any options
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
    # GIVEN case id not in database
    assert not taxprofiler_context.status_db.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )

    # WHEN running command with non-existing case-id
    result = cli_runner.invoke(metrics_deliver, [case_id_does_not_exist], obj=taxprofiler_context)
    # THEN command should NOT successfully call the command it creates

    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case id
    assert case_id_does_not_exist in caplog.text
    assert f"{case_id_does_not_exist} could not be found" in caplog.text


def test_metrics_deliver(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    taxprofiler_mock_analysis_finish,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
    taxprofiler_metrics_deliverables: Path,
):
    """Test command with a case id and a finished analysis which should execute successfully."""
    caplog.set_level(logging.INFO)

    # GIVEN case id
    result = cli_runner.invoke(metrics_deliver, [taxprofiler_case_id], obj=taxprofiler_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN metrics deliverable file should be generated
    assert taxprofiler_metrics_deliverables.is_file()

    # WHEN reading metrics_deliverable_content as yaml
    metrics_deliverables_content = read_yaml(file_path=taxprofiler_metrics_deliverables)

    assert isinstance(metrics_deliverables_content, dict)

    # THEN the metrics_deliverables_content contains the key "metrics"
    assert "metrics" in metrics_deliverables_content.keys()

    # THEN taxprofiler and case_id should be found in command string
    assert "Writing metrics deliverables file to" in caplog.text
