"""This script tests the cli methods to auto run balsamic"""
from cg.cli.balsamic import auto

EXIT_SUCCESS = 0


def test_dry(cli_runner, base_context):
    """Test command with --dry option"""

    # GIVEN case-id

    # WHEN dry running
    result = cli_runner.invoke(auto, ['--dry-run'], obj=base_context)

    # THEN command should have accepted the option happily
    assert result.exit_code == EXIT_SUCCESS


def test_balsamic_case_included(cli_runner, base_context, balsamic_case, caplog):
    """Test command with a balsamic case"""

    # GIVEN a case that is ready for Balsamic analysis
    #   -> has a sample that is sequenced and has a
    # balsamic data_type
    for link in balsamic_case.links:
        sample = link.sample
        assert sample.sequenced_at
        assert 'balsamic' in sample.data_analysis
    assert not balsamic_case.analyses

    # WHEN running command
    result = cli_runner.invoke(auto, ['--dry-run'], obj=base_context)

    # THEN command should have printed the case id
    assert result.exit_code == EXIT_SUCCESS
    assert balsamic_case.internal_id in caplog.text


def test_mip_only_case_excluded(cli_runner, base_context, mip_case, caplog):
    """Test command with a balsamic case"""

    # GIVEN a case that is ready for Balsamic analysis
    #   -> has a sample that is sequenced and has a
    # balsamic data_type
    for link in mip_case.links:
        sample = link.sample
        assert sample.sequenced_at
        assert 'balsamic' not in sample.data_analysis
    assert not mip_case.analyses

    # WHEN running command
    result = cli_runner.invoke(auto, ['--dry-run'], obj=base_context)

    # THEN command should not have printed the case id
    assert result.exit_code == EXIT_SUCCESS
    assert mip_case.internal_id not in caplog.text
