"""This script tests the cli method to clean old balsamic run dirs"""
from cg.cli.clean import balsamic_past_run_dirs

EXIT_SUCCESS = 0


def test_without_options(cli_runner, base_context):
    """Test command without options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_past_run_dirs, obj=base_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output
