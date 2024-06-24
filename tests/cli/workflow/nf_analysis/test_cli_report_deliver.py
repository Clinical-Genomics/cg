"""Tests CLI common methods to create the report_deliver for NF analyses."""

import logging
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.constants.constants import FileFormat
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS
from cg.io.controller import ReadFile
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_report_deliver_without_options(
    cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest
):
    """Test report-deliver for workflow without options."""
    # GIVEN a NextFlow analysis context
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # WHEN invoking the command without additional parameters
    result = cli_runner.invoke(workflow_cli, [workflow, "report-deliver"], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_report_deliver_with_missing_case(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    request: FixtureRequest,
):
    """Test report-deliver command for workflow with invalid case to start with."""
    caplog.set_level(logging.WARNING)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id not present in StatusDB
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN generating deliverables file
    result = cli_runner.invoke(
        workflow_cli, [workflow, "report-deliver", case_id_does_not_exist], obj=context
    )

    # THEN command should NOT succeed
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing the invalid case id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_report_deliver_without_samples(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
    request: FixtureRequest,
):
    """Test report-deliver command for workflow with case id and no samples."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = no_sample_case_id

    # WHEN generating deliverables with dry-run specified
    result = cli_runner.invoke(
        workflow_cli, [workflow, "report-deliver", case_id, "--dry-run"], obj=context
    )

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no samples exist in case
    assert "no samples" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_report_deliver_successful(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    deliverables_template_content: list[dict],
    mocker,
    request: FixtureRequest,
):
    """Test that deliverable files is properly created on a valid and successful run for workflow."""
    caplog.set_level(logging.INFO)

    # GIVEN deliverable files for a case and workflow
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    deliverables_file_path: Path = request.getfixturevalue(f"{workflow}_deliverables_file_path")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")

    # GIVEN a successful run

    # GIVEN a mocked deliverables template
    mocker.patch.object(
        NfAnalysisAPI,
        "get_deliverables_template_content",
        return_value=deliverables_template_content,
    )

    # WHEN running the command
    result = cli_runner.invoke(workflow_cli, [workflow, "report-deliver", case_id], obj=context)

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
