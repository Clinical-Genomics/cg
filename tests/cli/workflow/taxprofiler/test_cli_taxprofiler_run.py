"""This script tests the run cli command"""
import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import run
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


