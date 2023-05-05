"""Tests cli methods to create the case config for Taxprofiler"""

import logging
from pathlib import Path
from typing import List

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.taxprofiler.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_without_options(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test command without case_id."""
    # GIVEN NO case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=taxprofiler_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.NOTSET)
    # GIVEN case_id not in database
    assert not taxprofiler_context.status_db.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )
    # WHEN running
    result = cli_runner.invoke(config_case, [case_id_does_not_exist], obj=taxprofiler_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert "Case could not be found in StatusDB!" in result.output
    # assert "could not be found in StatusDB!" in caplog.text


# def test_without_samples(
#    cli_runner: CliRunner,
#    rnafusion_context: CGConfig,
#    caplog: LogCaptureFixture,
#    no_sample_case_id: str,
# ):
#    """Test command with case_id and no samples."""
#    caplog.set_level(logging.ERROR)
#    # GIVEN case-id
#    case_id: str = no_sample_case_id
#    # WHEN running config case
#    result = cli_runner.invoke(config_case, [case_id], obj=rnafusion_context)
#    # THEN command should print the rnafusion command-string
#    assert result.exit_code != EXIT_SUCCESS
#    # THEN warning should be printed that no sample is found
#    assert case_id in caplog.text
#    assert "has no samples" in caplog.text
