"""This script tests the run cli command"""
import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import run
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test command without case_id argument."""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=taxprofiler_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


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

    # GIVEN a mocked config for taxprofiler

    # WHEN dry running with dry specified
    result = cli_runner.invoke(
        run, [case_id, "--dry-run", "--use-nextflow"], obj=taxprofiler_context
    )

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN command should use nextflow
    assert "using nextflow" in caplog.text
    assert "path/to/bin/nextflow" in caplog.text
    assert "-work-dir" in caplog.text

    # THEN command should include resume flag
    assert "-resume" in caplog.text
