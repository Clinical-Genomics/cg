"""This script tests the cli methods to create prerequisites and start a mip-dna analysis"""
import logging

from cg.cli.workflow.mip_dna.base import start
from cg.constants import EXIT_SUCCESS, Pipeline


def test_dry(cli_runner, mip_context):
    """Test command with --dry option"""

    # GIVEN case-id

    # WHEN dry running
    result = cli_runner.invoke(start, ["--dry-run"], obj=mip_context)

    # THEN command should have accepted the option happily
    assert result.exit_code == EXIT_SUCCESS


def test_dna_case_included(cli_runner, mip_context, dna_case, caplog):
    """Test command with a dna case"""

    # GIVEN a case that is ready for MIP DNA analysis
    #   -> has a sample that is sequenced and has an dna-application (non-wts)
    for link in dna_case.links:
        sample = link.sample
        assert sample.sequenced_at
        assert sample.application_version.application.analysis_type not in "wts"
    assert not dna_case.analyses

    # WHEN running command
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(start, ["--dry-run"], obj=mip_context)

    # THEN command should have printed the case id
    assert result.exit_code == EXIT_SUCCESS
    case_mentioned = False
    for _, level, message in caplog.record_tuples:
        if dna_case.internal_id in message:
            case_mentioned = True
            assert level == logging.INFO
    assert case_mentioned


def test_rna_case_excluded(cli_runner, mip_context, rna_case, caplog):
    """Test command with a rna case"""

    # GIVEN a case that is ready for MIP RNA analysis
    #   -> has a sample that is sequenced and has an rna-application (wts)

    assert rna_case.data_analysis == str(Pipeline.MIP_RNA)
    for link in rna_case.links:
        sample = link.sample
        assert sample.sequenced_at

    # WHEN running command
    result = cli_runner.invoke(start, ["--dry-run"], obj=mip_context)

    # THEN command should not mention the rna-case
    assert result.exit_code == EXIT_SUCCESS

    case_mentioned = False
    for _, level, message in caplog.record_tuples:
        if rna_case.internal_id in message:
            case_mentioned = True
            assert level == logging.WARNING
    assert not case_mentioned


def test_rna_case_excluded(cli_runner, mip_context, dna_rna_mix_case, caplog, tb_api):
    """Test command with a mixed dna/rna case"""

    # GIVEN a case that is ready for MIP RNA analysis
    #   -> has a sample that is sequenced and has an rna-application (wts)

    rna_sample_found = False
    non_rna_sample_found = False
    assert dna_rna_mix_case.data_analysis == str(Pipeline.MIP_DNA)
    for link in dna_rna_mix_case.links:
        sample = link.sample
        assert sample.sequenced_at
        if sample.application_version.application.analysis_type in "wts":
            rna_sample_found = True
        if sample.application_version.application.analysis_type not in "wts":
            non_rna_sample_found = True
    assert not dna_rna_mix_case.analyses
    assert rna_sample_found
    assert non_rna_sample_found

    # WHEN running command
    result = cli_runner.invoke(start, ["--dry-run"], obj=mip_context)

    # THEN command should info about it starting the case but warn about skipping
    assert result.exit_code == EXIT_SUCCESS

    case_mentioned = False
    for _, level, message in caplog.record_tuples:
        if dna_rna_mix_case.internal_id in message:
            case_mentioned = True
            assert level == logging.WARNING
    assert case_mentioned
