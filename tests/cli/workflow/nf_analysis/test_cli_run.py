"""This script tests the run cli command"""

import logging

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS
from cg.models.cg_config import CGConfig


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_run_without_options(cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest):
    """Test run command for workflow without options."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN no case id

    # WHEN invoking the command without additional parameters
    result = cli_runner.invoke(workflow_cli, [workflow, "run"], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_run_with_missing_case(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    request: FixtureRequest,
):
    """Test run command for workflow with a missing case."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case not in the StatusDB database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running
    result = cli_runner.invoke(workflow_cli, [workflow, "run", case_id_does_not_exist], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN the error log should indicate that the case is invalid
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_run_case_without_samples(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
    request: FixtureRequest,
):
    """Test command with a case lacking linked samples."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case without linked samples

    # WHEN invoking the command
    result = cli_runner.invoke(
        workflow_cli, [workflow, "run", no_sample_case_id, "--dry-run"], obj=context
    )

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no sample is found
    assert no_sample_case_id in caplog.text
    assert "no samples" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_run_case_without_config_files(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test command with case_id and no config file."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # WHEN invoking a run command
    result = cli_runner.invoke(workflow_cli, [workflow, "run", case_id], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN the error log should indicate that the config file is missing
    assert "No config file found" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_run_case_from_start_dry_run(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test dry-run for a case with existing config files."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN mocked config files
    request.getfixturevalue(f"{workflow}_mock_config")

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(
        workflow_cli, [workflow, "run", case_id, "--from-start", "--dry-run"], obj=context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower
    assert "using Tower" in caplog.text
    assert "path/to/bin/tw launch" in caplog.text
    assert "--work-dir" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_run_case_with_revision_dry_run(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test dry-run for a case with existing config files with a given revision."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked config
    request.getfixturevalue(f"{workflow}_mock_config")

    # WHEN invoking a command with dry-run and revision specified
    result = cli_runner.invoke(
        workflow_cli,
        [workflow, "run", case_id, "--dry-run", "--from-start", "--revision", "2.1.0"],
        obj=context,
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use the specified revision
    assert "--revision 2.1.0" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_resume_case_dry_run(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    tower_id,
    request: FixtureRequest,
):
    """Test dry-run to resume a case with existing config fjles."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked config
    # request.getfixturevalue(f"{workflow}_mock_config")

    # WHEN invoking a command with dry-run and nf-tower-id specified
    result = cli_runner.invoke(
        workflow_cli,
        [workflow, "run", case_id, "--nf-tower-id", tower_id, "--dry-run"],
        obj=context,
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower for relaunch
    assert "Workflow will be resumed from run" in caplog.text
    assert "tw runs relaunch" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_resume_case_with_missing_tower_id(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    raredisease_mock_config,
    request: FixtureRequest,
):
    """Test resume command without providing NF-Tower ID and without existing Trailblazer config file."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    cli_runner.invoke(workflow_cli, [workflow, "run", case_id, "--dry-run"], obj=context)

    # THEN command should raise error
    assert "Could not resume analysis: No NF-Tower ID found for case" in caplog.text
    pytest.raises(FileNotFoundError)


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS,
)
def test_resume_using_nextflow_dry_run(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    raredisease_mock_config,
    request: FixtureRequest,
):
    """Test command with case_id and config file using nextflow."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(
        workflow_cli, [workflow, "run", case_id, "--dry-run", "--use-nextflow"], obj=context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use nextflow
    assert "using Nextflow" in caplog.text
    assert "path/to/bin/nextflow" in caplog.text
    assert "-work-dir" in caplog.text

    # THEN command should include resume flag
    assert "-resume" in caplog.text
