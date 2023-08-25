"""Tests for the report-deliver cli command"""

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import report_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import FileDeliverable


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


def test_successful(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    rnafusion_deliverables_file_path: Path,
    mock_analysis_finish,
):
    """Test that deliverable files is properly created on a valid and successful run."""
    caplog.set_level(logging.INFO)

    # GIVEN a successful run

    # WHEN dry running with dry specified
    result = cli_runner.invoke(report_deliver, [rnafusion_case_id], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN deliverables file should be written
    assert rnafusion_deliverables_file_path.is_file()

    # THEN deliverables content should match the expected values
    with rnafusion_deliverables_file_path.open("r") as file:
        content = file.read()
        for field in FileDeliverable.__annotations__.keys():
            assert field in content
        # Optional fields should be properly written
        # TODO: fix this
        # assert "null" not in content
        # assert "'~'" in content
