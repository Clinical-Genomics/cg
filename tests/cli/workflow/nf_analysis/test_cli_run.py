"""This script tests the run cli command"""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.raredisease.base import run
from cg.cli.workflow.rnafusion.base import run
from cg.cli.workflow.taxprofiler.base import run
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.models.cg_config import CGConfig


@pytest.mark.parametrize(
    "context", ["raredisease_context", "rnafusion_context", "taxprofiler_context"]
)
def test_without_options(cli_runner: CliRunner, context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "context", ["raredisease_context", "rnafusion_context", "taxprofiler_context"]
)
def test_with_missing_case(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    request,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN a case id not in database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)
    # WHEN running
    result = cli_runner.invoke(run, [case_id_does_not_exist], obj=context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text


@pytest.mark.parametrize(
    "context", ["raredisease_context", "rnafusion_context", "taxprofiler_context"]
)
def test_without_samples(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
    request,
):
    """Test command with case_id and no samples."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = no_sample_case_id
    # WHEN invoking the command with dry-run specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert case_id in caplog.text
    assert "no samples" in caplog.text


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_without_config_dry_run(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    request,
):
    """Test command dry-run with case_id and no config file."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(run, [case_id, "--from-start", "--dry-run"], obj=context)
    # THEN command should execute successfully (dry-run)
    assert result.exit_code == EXIT_SUCCESS


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_without_config(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    request,
):
    """Test command with case_id and no config file."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)
    # WHEN invoking a run command
    result = cli_runner.invoke(run, [case_id], obj=context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_with_config(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    mock_config,
    request,
):
    """Test command with case_id and config file using tower."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)
    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(run, [case_id, "--from-start", "--dry-run"], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower
    assert "using Tower" in caplog.text
    assert "path/to/bin/tw launch" in caplog.text
    assert "--work-dir" in caplog.text


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_with_revision(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    mock_config,
    request,
):
    """Test command with case_id and config file using tower and specifying a revision."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--from-start", "--revision", "2.1.0"], obj=context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower
    assert "--revision 2.1.0" in caplog.text


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_resume_with_id(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    mock_config,
    tower_id,
    request,
):
    """Test resume command given a NF-Tower run ID using Tower."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN a case-id
    case_id: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(run, [case_id, "--nf-tower-id", tower_id, "--dry-run"], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower for relaunch
    assert "Workflow will be resumed from run" in caplog.text
    assert "tw runs relaunch" in caplog.text


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_resume_without_id_error(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    mock_config,
    request,
):
    """Test resume command without providing NF-Tower ID and without existing Trailblazer Tower config file."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    cli_runner.invoke(run, [case_id, "--dry-run"], obj=context)

    # THEN command should raise error
    assert "Could not resume analysis: No NF-Tower ID found for case" in caplog.text
    pytest.raises(FileNotFoundError)


@pytest.mark.parametrize(
    "context,case_id",
    [
        ("raredisease_context", "raredisease_case_id"),
        ("rnafusion_context", "rnafusion_case_id"),
        ("taxprofiler_context", "taxprofiler_case_id"),
    ],
)
def test_with_config_use_nextflow(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    mock_config,
    request,
):
    """Test command with case_id and config file using nextflow."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN a case id
    case_id: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # WHEN invoking a command with dry-run specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", "--use-nextflow"], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use nextflow
    assert "using Nextflow" in caplog.text
    assert "path/to/bin/nextflow" in caplog.text
    assert "-work-dir" in caplog.text

    # THEN command should include resume flag
    assert "-resume" in caplog.text
