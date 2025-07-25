"""This script tests the cli methods to create prerequisites and start a mip-dna analysis"""

import logging
from unittest import mock

from click.testing import CliRunner

from cg.cli.workflow.mip_dna.base import start_available
from cg.constants import EXIT_SUCCESS, Workflow
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig


def test_dry(cli_runner, mip_dna_context, caplog):
    """Test mip-dna start-available with --dry option"""
    # GIVEN that the log messages are captured
    caplog.set_level(logging.INFO)

    # GIVEN a mip_dna_context with 3 cases that are ready for analysis
    analysis_api = MipDNAAnalysisAPI(config=mip_dna_context)
    assert len(analysis_api.get_cases_to_analyze()) == 3

    # GIVEN that the cases do not need decompression
    with mock.patch.object(MipDNAAnalysisAPI, "resolve_decompression", return_value=None):

        # WHEN using dry running
        result = cli_runner.invoke(start_available, ["--dry-run"], obj=mip_dna_context)

    # THEN command should have accepted the option happily
    assert result.exit_code == EXIT_SUCCESS

    # THEN that the 3 cases are picked up to start
    assert caplog.text.count("Starting full MIP analysis workflow for case") == 3


def test_start_available_with_limit(
    cli_runner: CliRunner,
    caplog,
    mip_dna_context: CGConfig,
    mip_dna_analysis_api: MipDNAAnalysisAPI,
):
    """Test that the mip-dna start-available command picks up only the given max number of cases."""
    # GIVEN that the log messages are captured
    caplog.set_level(logging.INFO)

    # GIVEN a mip_dna_context with 3 cases that are ready for analysis
    assert len(mip_dna_analysis_api.get_cases_to_analyze()) == 3

    # GIVEN that the cases do not need decompression
    with mock.patch.object(MipDNAAnalysisAPI, "resolve_decompression", return_value=None):

        # WHEN running start-available command with limit=1
        result = cli_runner.invoke(
            start_available, ["--dry-run", "--limit", 1], obj=mip_dna_context
        )

    # THEN command succeeds
    assert result.exit_code == EXIT_SUCCESS

    # THEN only 1 case is picked up to start
    assert caplog.text.count("Starting full MIP analysis workflow for case") == 1


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
