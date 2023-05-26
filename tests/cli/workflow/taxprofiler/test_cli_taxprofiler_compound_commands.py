from click.testing import CliRunner
from cg.cli.workflow.taxprofiler.base import (
    taxprofiler,
)
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_taxprofiler_no_args(cli_runner: CliRunner, taxprofiler_context: CGConfig):
    """Test to see that running Taxprofiler without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(taxprofiler, [], obj=taxprofiler_context)

    assert result.exit_code == EXIT_SUCCESS

    ## THEN help should be printed
    assert "help" in result.output
