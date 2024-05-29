"""This script tests the CLI method enable workflows."""

from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cmd
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_no_options(cli_runner: CliRunner, base_context: CGConfig):
    """Test command with no options."""
    # GIVEN
    # WHEN dry running
    result = cli_runner.invoke(workflow_cmd, obj=base_context)

    # THEN command should have returned all pipelines that is supported
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert "balsamic-qc" in result.output
    assert "balsamic-umi" in result.output
    assert "microsalt" in result.output
    assert "mip-dna" in result.output
    assert "mip-rna" in result.output
    assert "raredisease" in result.output
    assert "rnafusion" in result.output
    assert "taxprofiler" in result.output
