"""This module tests the run CLI command."""

import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import run
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


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
        "using Nextflow",
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
        "using Tower",
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
    assert "Workflow will be resumed from run" in caplog.text
    assert "path/to/bin/tw runs relaunch" in caplog.text
