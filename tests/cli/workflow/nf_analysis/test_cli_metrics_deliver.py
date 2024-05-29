"""Tests CLI common methods to create the case config for NF analyses."""

import logging
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.io.yaml import read_yaml
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_metrics_deliver_without_options(
    cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest
):
    """Test metrics-deliver for workflow without options."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # WHEN invoking the command without additional parameters
    result = cli_runner.invoke(workflow_cli, [workflow, "metrics-deliver"], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_metrics_deliver_with_missing_case(
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    workflow: Workflow,
    request: FixtureRequest,
):
    """Test metrics-deliver for workflow with a missing case."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case not in the StatusDB database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running
    result = cli_runner.invoke(
        workflow_cli, [workflow, "metrics-deliver", case_id_does_not_exist], obj=context
    )

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_metrics_deliver_case(
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    workflow: Workflow,
    request: FixtureRequest,
):
    """Test command with a case id and a finished analysis which should execute successfully."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case for which we mocked files created after a successful run
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    metrics_deliverables_path: Path = request.getfixturevalue(
        f"{workflow}_metrics_deliverables_path"
    )
    request.getfixturevalue(f"{workflow}_mock_deliverable_dir")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")

    # WHEN invoking the command
    result = cli_runner.invoke(workflow_cli, [workflow, "metrics-deliver", case_id], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN metrics deliverable file should be generated
    assert "Writing metrics deliverables file to" in caplog.text
    assert metrics_deliverables_path.is_file()

    # WHEN reading metrics_deliverable_content as yaml
    metrics_deliverables_content = read_yaml(file_path=metrics_deliverables_path)
    assert isinstance(metrics_deliverables_content, dict)

    # THEN the metrics_deliverables file contains the key "metrics"
    assert "metrics" in metrics_deliverables_content.keys()
