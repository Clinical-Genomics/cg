"""This script tests the cli methods to create prerequisites and start a mip-dna analysis"""
import logging

from cg.cli.workflow.mip_dna.base import start, start_available
from cg.constants import EXIT_SUCCESS, Pipeline
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI


def test_dry(cli_runner, dna_mip_context):
    """Test mip dna start with --dry option"""

    # GIVEN a dna_mip_context

    # WHEN using dry running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=dna_mip_context)

    # THEN command should have accepted the option happily
    assert result.exit_code == EXIT_SUCCESS


def test_dna_case_included(cli_runner, caplog, dna_case, dna_mip_context, mocker):
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
        assert sample.sequenced_at
        assert sample.application_version.application.analysis_type not in "wts"
    assert not dna_case.analyses

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=dna_mip_context)

    # THEN command should have printed the case id
    assert result.exit_code == EXIT_SUCCESS


def test_rna_case_excluded(cli_runner, caplog, dna_mip_context, rna_case, mocker):
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

    assert rna_case.data_analysis == str(Pipeline.MIP_RNA)
    for link in rna_case.links:
        sample = link.sample
        assert sample.sequenced_at

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=dna_mip_context)

    # THEN command should not mention the rna-case
    assert result.exit_code == EXIT_SUCCESS
    assert rna_case.internal_id not in caplog.text


def test_mixed_dna_rna_case(cli_runner, caplog, dna_mip_context, dna_rna_mix_case, mocker):
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
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=dna_mip_context)

    # THEN command should info about it starting the case but warn about skipping
    assert result.exit_code == EXIT_SUCCESS
