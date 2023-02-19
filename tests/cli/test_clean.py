from click.testing import CliRunner

from cg.cli.clean import fix_flow_cell_status
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_fix_flow_cell_status(
    cli_runner: CliRunner,
    base_context: CGConfig,
):
    """Test fix flow cell status command."""
    # Given a base context

    # WHEN running command
    result = cli_runner.invoke(fix_flow_cell_status, obj=base_context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS
