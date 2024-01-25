"""Tests for the metrics-deliver CLI command."""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import metrics_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.io.yaml import read_yaml


def test_metrics_deliver(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    taxprofiler_mock_analysis_finish,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
    taxprofiler_metrics_deliverables_path: Path,
):
    """Test command with a case id and a finished analysis which should execute successfully."""
    caplog.set_level(logging.INFO)

    # GIVEN case id
    result = cli_runner.invoke(metrics_deliver, [taxprofiler_case_id], obj=taxprofiler_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN metrics deliverable file should be generated
    assert taxprofiler_metrics_deliverables_path.is_file()

    # WHEN reading metrics_deliverable_content as yaml
    metrics_deliverables_content = read_yaml(file_path=taxprofiler_metrics_deliverables_path)

    assert isinstance(metrics_deliverables_content, dict)

    # THEN the metrics_deliverables_content contains the key "metrics"
    assert "metrics" in metrics_deliverables_content.keys()

    # THEN taxprofiler and case_id should be found in command string
    assert "Writing metrics deliverables file to" in caplog.text
