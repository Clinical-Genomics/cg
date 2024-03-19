"""Tests CLI common methods to create the case config for NF analyses."""

import logging
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import WorkflowParameters

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_config_case_without_options(
    cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest
):
    """Test config_case for workflow without options."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # WHEN dry running without anything specified
    result = cli_runner.invoke(workflow_cli, [workflow, "config-case"], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_config_case_with_missing_case(
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    workflow: Workflow,
    request: FixtureRequest,
):
    """Test config_case for workflow with a missing case."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case not in the StatusDB database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running
    result = cli_runner.invoke(
        workflow_cli, [workflow, "config-case", case_id_does_not_exist], obj=context
    )

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN the error log should indicate that the case is invalid
    assert "could not be found in Status DB!" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.RAREDISEASE, Workflow.TOMTE],
)
def test_config_case_without_samples(
    cli_runner: CliRunner,
    workflow: Workflow,
    no_sample_case_id: str,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test command with a case lacking linked samples."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case without linked samples

    # WHEN invoking the command
    result = cli_runner.invoke(
        workflow_cli, [workflow, "config-case", no_sample_case_id], obj=context
    )

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no sample is found
    assert no_sample_case_id in caplog.text
    assert "has no samples" in caplog.text


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.RAREDISEASE, Workflow.TOMTE],
)
def test_config_case_default_parameters(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test that command generates config files."""
    caplog.set_level(logging.DEBUG)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    sample_sheet_path: Path = request.getfixturevalue(f"{workflow}_sample_sheet_path")
    params_file_path: Path = request.getfixturevalue(f"{workflow}_params_file_path")
    nexflow_config_file_path: Path = request.getfixturevalue(f"{workflow}_nexflow_config_file_path")
    sample_sheet_content_expected: str = request.getfixturevalue(f"{workflow}_sample_sheet_content")

    # GIVEN a valid case

    # WHEN running config case
    result = cli_runner.invoke(workflow_cli, [workflow, "config-case", case_id], obj=context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN logs should be as expected
    expected_logs: list[str] = [
        "Getting sample sheet information",
        "Writing sample sheet",
        "Getting parameters information",
        "Writing parameters file",
        "Writing nextflow config file",
    ]
    for expected_log in expected_logs:
        assert expected_log in caplog.text

    # THEN config files should be generated
    assert sample_sheet_path.is_file()
    assert params_file_path.is_file()
    assert nexflow_config_file_path.is_file()

    # THEN the sample sheet content should match the expected values
    sample_sheet_content_created: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.TXT, file_path=sample_sheet_path, read_to_string=True
    )
    assert sample_sheet_content_expected in sample_sheet_content_created

    # WHEN workflow is not raredisease
    # Note this will need to be unified once all workflows are standarised
    if workflow not in {Workflow.RAREDISEASE, Workflow.TOMTE}:
        # THEN the params file should contain all parameters
        parameters_default = vars(request.getfixturevalue(f"{workflow}_parameters_default"))
        params_content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.TXT, file_path=params_file_path, read_to_string=True
        )
        for parameter in parameters_default:
            assert parameter in params_content


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.RAREDISEASE, Workflow.TOMTE],
)
def test_config_case_dry_run(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test dry-run."""
    caplog.set_level(logging.DEBUG)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    sample_sheet_path: Path = request.getfixturevalue(f"{workflow}_sample_sheet_path")
    params_file_path: Path = request.getfixturevalue(f"{workflow}_params_file_path")
    nexflow_config_file_path: Path = request.getfixturevalue(f"{workflow}_nexflow_config_file_path")

    # GIVEN a valid case

    # WHEN invoking the command with dry-run specified
    result = cli_runner.invoke(workflow_cli, [workflow, "config-case", case_id, "-d"], obj=context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN sample sheet and parameters information should be collected
    assert "Getting sample sheet information" in caplog.text
    assert "Getting parameters information" in caplog.text

    # THEN sample sheet and parameters information files should not be written
    assert "Dry run: Config files will not be written" in caplog.text
    assert "Writing sample sheet" not in caplog.text
    assert "Writing parameters file" not in caplog.text
    assert not sample_sheet_path.is_file()
    assert not params_file_path.is_file()
    assert not nexflow_config_file_path.is_file()
