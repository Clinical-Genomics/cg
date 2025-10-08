"""This script tests the cli methods to create prerequisites and start a mip-dna analysis"""

import logging
from typing import cast
from unittest.mock import Mock, create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.mip.base import start_available
from cg.constants import EXIT_SUCCESS, Workflow
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
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


def test_dna_case_included(cli_runner, caplog, dna_case, mip_dna_context, mocker):
    """Test mip dna start with a DNA case"""

    caplog.set_level(logging.INFO)

    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN there is spring files that can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = True

    # GIVEN a case that is ready for MIP DNA analysis
    #   -> has a sample that is sequenced and has an dna-application (non-wts)
    for link in dna_case.links:
        sample = link.sample
        assert sample.last_sequenced_at
        assert sample.application_version.application.analysis_type not in "wts"
    assert not dna_case.analyses

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=mip_dna_context)

    # THEN command should have printed the case id
    assert result.exit_code == EXIT_SUCCESS


def test_rna_case_excluded(cli_runner, caplog, mip_dna_context, rna_case, mocker):
    """Test mip dna start with a RNA case"""

    caplog.set_level(logging.INFO)

    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN there is spring files that can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = True

    # GIVEN a case that is ready for MIP RNA analysis
    #   -> has a sample that is sequenced and has an rna-application (wts)

    assert rna_case.data_analysis == Workflow.MIP_RNA
    for link in rna_case.links:
        sample = link.sample
        assert sample.last_sequenced_at

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=mip_dna_context)

    # THEN command should not mention the rna-case
    assert result.exit_code == EXIT_SUCCESS
    assert rna_case.internal_id not in caplog.text


def test_mixed_dna_rna_case(cli_runner, caplog, mip_dna_context, dna_rna_mix_case, mocker):
    """Test mip dna start with a mixed DNA/RNA case"""
    caplog.set_level(logging.INFO)
    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN there is spring files that can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = True

    # GIVEN a case that is ready for MIP RNA analysis
    #   -> has a sample that is sequenced and has an rna-application (wts)
    assert not dna_rna_mix_case.analyses

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=mip_dna_context)

    # THEN command should info about it starting the case but warn about skipping
    assert result.exit_code == EXIT_SUCCESS
