import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.raredisease.base import raredisease
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_raredisease_no_args(cli_runner: CliRunner, raredisease_context: CGConfig):
    """Test to see that running RAREDISEASE without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(raredisease, [], obj=raredisease_context)

    # THEN command runs successfully
    print(result.output)

    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output
