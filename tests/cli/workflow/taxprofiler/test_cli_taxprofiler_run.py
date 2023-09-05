"""This module tests the run CLI command."""
import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import run
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test command without case id argument."""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=taxprofiler_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
):
    """Test run command with invalid case."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    assert not taxprofiler_context.status_db.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )
    # WHEN running
    result = cli_runner.invoke(run, [case_id_does_not_exist], obj=taxprofiler_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert f"{case_id_does_not_exist} could not be found" in caplog.text


def test_with_config_use_nextflow(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
    taxprofiler_config,
):
    """Test command with case_id and config file using nextflow."""
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id: str = taxprofiler_case_id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--use-nextflow"], obj=taxprofiler_context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    for message in [
        "using nextflow",
        "path/to/bin/nextflow",
        "-work-dir",
        "-params-file",
        "-resume",
    ]:
        assert message in caplog.text


def test_with_config_use_tower(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
    taxprofiler_config,
):
    """Test command with case_id and config file using tower."""
    caplog.set_level(logging.INFO)
    # GIVEN  a valid case
    case_id: str = taxprofiler_case_id

    # GIVEN a mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(run, [case_id, "--from-start", "--dry-run"], obj=taxprofiler_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower

    for message in [
        "using tower",
        "path/to/bin/tw launch",
    ]:
        assert message in caplog.text


def test_with_config_use_tower_resume(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
    taxprofiler_config,
    tower_id,
):
    """Test resume command with tower to use tw run instead of tw launch."""
    caplog.set_level(logging.INFO)

    # GIVEN a taxprofiler case-id and mocked config

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        run, [taxprofiler_case_id, "--nf-tower-id", tower_id, "--dry-run"], obj=taxprofiler_context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use tower for relaunch
    assert "Pipeline will be resumed from run" in caplog.text
    assert "path/to/bin/tw runs relaunch" in caplog.text
