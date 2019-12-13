"""This script tests the cli method to do store analysis result files"""
from cg.cli.store.store import store

EXIT_SUCCESS = 0


def test_no_options(cli_runner, base_context):
    """Test command with no options"""

    # GIVEN

    # WHEN dry running
    result = cli_runner.invoke(store, obj=base_context)

    # THEN command should have returned all pipelines that is supported
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert "microsalt" in result.output
    assert "mip-dna" in result.output
    assert "mip-rna" in result.output
