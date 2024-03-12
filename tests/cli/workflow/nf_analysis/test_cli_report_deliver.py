"""Tests CLI common methods to create the report_deliver for NF analyses."""

import logging
import pytest
from pathlib import Path

from click.testing import CliRunner
from _pytest.logging import LogCaptureFixture

from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.cli.workflow.rnafusion.base import report_deliver
from cg.models.cg_config import CGConfig
from cg.constants import EXIT_SUCCESS
from cg.io.controller import ReadFile
from cg.constants.constants import FileFormat

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_report_deliver_without_options(cli_runner: CliRunner, context: CGConfig, request):
    """Test report-deliver for workflow without options."""
    # GIVEN a NextFlow analysis context
    context = request.getfixturevalue(context)

    # WHEN dry running without anything specified
    result = cli_runner.invoke(report_deliver, obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_report_deliver_with_missing_case(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    request,
):
    """Test report-deliver command for workflow with invalid case to start with."""
    caplog.set_level(logging.WARNING)
    context = request.getfixturevalue(context)

    # GIVEN case_id not in database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN generating deliverables file
    result = cli_runner.invoke(report_deliver, [case_id_does_not_exist], obj=context)

    # THEN command should NOT succeed
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing the invalid case id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_report_deliver_without_samples(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
    request,
):
    """Test report-deliver command for workflow with case id and no samples."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN case-id
    case_id: str = no_sample_case_id

    # WHEN generating deliverables with dry specified
    result = cli_runner.invoke(report_deliver, [case_id, "--dry-run"], obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no samples exist in case
    assert "no samples" in caplog.text


@pytest.mark.parametrize(
    ("context", "case_id", "deliverables_file_path", "mock_analysis_finish"),
    [
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
            "taxprofiler_deliverables_file_path",
            "taxprofiler_mock_analysis_finish",
        ),
        (
            "rnafusion_context",
            "rnafusion_case_id",
            "rnafusion_deliverables_file_path",
            "rnafusion_mock_analysis_finish",
        ),
    ],
)
def test_report_deliver_successful(
    cli_runner: CliRunner,
    context: CGConfig,
    case_id: str,
    deliverables_file_path: Path,
    deliverables_template_content: list[dict],
    mock_analysis_finish,
    caplog: LogCaptureFixture,
    mocker,
    request,
):
    """Test that deliverable files is properly created on a valid and successful run for workflow."""
    caplog.set_level(logging.INFO)

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(context)
    deliverables_file_path: dict = request.getfixturevalue(deliverables_file_path)
    case_id: str = request.getfixturevalue(case_id)
    request.getfixturevalue(mock_analysis_finish)

    # GIVEN a successful run

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        NfAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # WHEN running the command
    result = cli_runner.invoke(report_deliver, [case_id], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN deliverables file should be written
    assert deliverables_file_path.is_file()

    # THEN deliverables content should match the expected values
    deliverables_content: str = ReadFile.get_content_from_file(
        file_format=FileFormat.TXT, file_path=deliverables_file_path, read_to_string=True
    )
    for field in deliverables_template_content[0].keys():
        assert field in deliverables_content

    # THEN assess that missing fields are written
    assert "path_index: null" in deliverables_content
