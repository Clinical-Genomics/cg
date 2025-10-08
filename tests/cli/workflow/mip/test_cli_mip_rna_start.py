"""This script tests the cli methods to create prerequisites and start a mip-rna analysis"""

import logging
from typing import cast
from unittest.mock import Mock, create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.mip.base import start_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store


def test_start_available_mip_rna(cli_runner, mip_rna_context, caplog, mocker: MockerFixture):
    """Test mip-rna start-available with --dry option"""
    # GIVEN that the log messages are captured
    caplog.set_level(logging.INFO)

    # GIVEN a mip_rna_context with 1 case that is ready for analysis
    analysis_api: MipRNAAnalysisAPI = create_autospec(MipRNAAnalysisAPI)
    analysis_api.get_cases_to_analyze = Mock(
        return_value=[create_autospec(Case, internal_id="case_id")]
    )
    analysis_api.status_db = create_autospec(Store)
    mip_rna_context.meta_apis["analysis_api"] = analysis_api

    # WHEN using dry running
    result = cli_runner.invoke(
        start_available, ["--dry-run"], obj=mip_rna_context, catch_exceptions=False
    )

    # THEN command should have accepted the option happily
    assert result.exit_code == EXIT_SUCCESS

    # THEN the case is picked up to start
    assert caplog.text.count("Starting full MIP analysis workflow for case") == 1


def test_start_available_with_limit(
    cli_runner: CliRunner,
    caplog,
    mip_rna_context: CGConfig,
):
    """Test that the mip-rna start-available command picks up only the given max number of cases."""
    # GIVEN that the log messages are captured
    caplog.set_level(logging.INFO)

    # GIVEN a mip_rna_context with cases that are ready for analysis
    analysis_api: MipRNAAnalysisAPI = create_autospec(MipRNAAnalysisAPI)
    analysis_api.get_cases_to_analyze = Mock(
        return_value=[
            create_autospec(Case, internal_id="case_id"),
        ]
    )
    analysis_api.status_db = create_autospec(Store)
    mip_rna_context.meta_apis["analysis_api"] = analysis_api

    # WHEN running start-available command with limit=1
    result = cli_runner.invoke(start_available, ["--dry-run", "--limit", "1"], obj=mip_rna_context)

    # THEN command succeeds
    assert result.exit_code == EXIT_SUCCESS

    # THEN the limit should have been used when getting cases to analyze
    cast(Mock, analysis_api.get_cases_to_analyze).assert_called_once_with(limit=1)

    # THEN only 1 case is picked up to start
    assert caplog.text.count("Starting full MIP analysis workflow for case") == 1
    assert "Starting 1 available MIP cases" in caplog.text
