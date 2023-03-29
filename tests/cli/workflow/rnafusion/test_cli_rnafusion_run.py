"""This script tests the run cli command"""
import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import run
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    not_existing_case_id: str,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    assert not rnafusion_context.status_db.get_case_by_internal_id(internal_id=not_existing_case_id)
    # WHEN running
    result = cli_runner.invoke(run, [not_existing_case_id], obj=rnafusion_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert not_existing_case_id in caplog.text
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
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert case_id in caplog.text
    assert "no samples" in caplog.text


def test_without_config(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with case_id and no config file."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id: str = rnafusion_case_id
    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=rnafusion_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_with_config_use_nextflow(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    mock_config,
):
    """Test command with case_id and config file using nextflow."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run", "--use-nextflow"], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use nextflow
    assert "using nextflow" in caplog.text
    assert "path/to/bin/nextflow" in caplog.text
    assert "-work-dir" in caplog.text

    # THEN command should include resume flag
    assert "-resume" in caplog.text


def test_with_config(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    mock_config,
):
    """Test command with case_id and config file using tower."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower
    assert "using tower" in caplog.text
    assert "path/to/bin/tw launch" in caplog.text
    assert "--work-dir" in caplog.text


def test_with_revision(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    mock_config,
):
    """Test command with case_id and config file using tower and specifying a revision."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = rnafusion_case_id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--revision", "2.1.0"], obj=rnafusion_context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower
    assert "--revision 2.1.0" in caplog.text
