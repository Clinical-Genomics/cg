"""This file groups all tests related to microsalt start creation"""

import logging
from pathlib import Path
from unittest.mock import PropertyMock, create_autospec

from click.testing import CliRunner

from cg.cli.workflow.microsalt.base import run
from cg.meta.workflow.microsalt.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner: CliRunner, base_context: CGConfig):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS


def test_dry_arguments(cli_runner: CliRunner, base_context: CGConfig, ticket_id, caplog):
    """Test command dry"""

    # GIVEN
    caplog.set_level(logging.INFO)

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, [ticket_id, "-t", "--dry-run"], obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code == EXIT_SUCCESS
    assert f"Running command" in caplog.text


def test_calls_on_analysis_started(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN an instance of the MicrosaltAnalysisAPI has been setup
    analysis_api: MicrosaltAnalysisAPI = create_autospec(
        MicrosaltAnalysisAPI,
        status_db=PropertyMock(
            return_value=create_autospec(Store),
        ),
    )
    base_context.meta_apis["analysis_api"] = analysis_api

    # GIVEN a case can be retrieved from the analysis api
    case_id = "some_case_id"
    analysis_api.resolve_case_sample_id = lambda sample, ticket, unique_id: (case_id, None)

    # WHEN successfully invoking the run command
    cli_runner.invoke(run, [case_id], obj=base_context)

    # THEN the on_analysis_started function has been called with the found case_id
    analysis_api.on_analysis_started.assert_called_with(case_id)
