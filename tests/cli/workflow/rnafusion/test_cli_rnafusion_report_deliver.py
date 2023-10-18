"""Tests for the report-deliver cli command"""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import report_deliver
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case_id

    # WHEN dry running without anything specified
    result = cli_runner.invoke(report_deliver, obj=rnafusion_context)

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
    result = cli_runner.invoke(report_deliver, [case_id_does_not_exist], obj=rnafusion_context)

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
    case_id: str = no_sample_case_id

    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no samples exist in case
    assert "no samples" in caplog.text


def test_report_deliver_successful(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    rnafusion_case_id: str,
    rnafusion_deliverables_file_path: Path,
    deliverables_template_content: list[dict],
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    mocker,
):
    """Test that deliverable files is properly created on a valid and successful run."""
    caplog.set_level(logging.INFO)

    # GIVEN a successful run

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        RnafusionAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # WHEN running
    result = cli_runner.invoke(report_deliver, [rnafusion_case_id], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN deliverables file should be written
    assert rnafusion_deliverables_file_path.is_file()

    # THEN deliverables content should match the expected values
    deliverables_content: str = ReadFile.get_content_from_file(
        file_format=FileFormat.TXT, file_path=rnafusion_deliverables_file_path, read_to_string=True
    )
    for field in deliverables_template_content[0].keys():
        assert field in deliverables_content
    # THEN assess that missing fields are written
    assert "path_index: null" in deliverables_content
