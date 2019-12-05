"""This script tests the cli methods to create the auto for a balsamic auto"""
import logging
from cg.cli.analysis.mip_rd_dna import auto

EXIT_SUCCESS = 0


def test_dry(cli_runner, base_context):
    """Test command with --dry option"""

    # GIVEN case-id

    # WHEN dry running
    result = cli_runner.invoke(auto, ['--dry-run'], obj=base_context)

    # THEN command should have accepted the option happily
    assert result.exit_code == EXIT_SUCCESS


def test_dna_case_included(cli_runner, base_context, dna_case, caplog):
    """Test command with a dna case"""

    # GIVEN a case that is ready for MIP DNA analysis
    #   -> has a sample that is sequenced and has an dna-application (non-wts)
    for link in dna_case.links:
        sample = link.sample
        assert sample.sequenced_at
        assert sample.application_version.application.analysis_type not in 'wts'
    assert not dna_case.analyses

    # WHEN running command
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(auto, ['--dry-run'], obj=base_context)

    # THEN command should have printed the case id
    assert result.exit_code == EXIT_SUCCESS
    case_mentioned = False
    for _, level, message in caplog.record_tuples:
        if dna_case.internal_id in message:
            case_mentioned = True
            assert level == logging.INFO
    assert case_mentioned


def test_rna_case_excluded(cli_runner, base_context, rna_case, caplog):
    """Test command with a rna case"""

    # GIVEN a case that is ready for MIP RNA analysis
    #   -> has a sample that is sequenced and has an rna-application (wts)
    for link in rna_case.links:
        sample = link.sample
        assert sample.sequenced_at
        assert sample.application_version.application.analysis_type in 'wts'
    assert not rna_case.analyses

    # WHEN running command
    result = cli_runner.invoke(auto, ['--dry-run'], obj=base_context)

    # THEN command should info about it starting the case but warn about skipping
    assert result.exit_code == EXIT_SUCCESS

    case_mentioned = False
    for _, level, message in caplog.record_tuples:
        if rna_case.internal_id in message:
            case_mentioned = True
            assert level == logging.WARNING
    assert case_mentioned
