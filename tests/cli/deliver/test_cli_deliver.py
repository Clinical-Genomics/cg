"""This script tests the cli method to deliver"""
from cg.cli.deliver.deliver import deliver

EXIT_SUCCESS = 0


def test_no_options(cli_runner, base_context):
    """Test command with no options"""

    # GIVEN

    # WHEN dry running
    result = cli_runner.invoke(deliver, obj=base_context)

    # THEN command should have returned all sub-commands happily
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert "microsalt" in result.output
    assert "mip-dna" in result.output
    assert "mip-rna" in result.output
