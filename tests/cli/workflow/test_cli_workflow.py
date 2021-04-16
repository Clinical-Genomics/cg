"""This script tests the cli method enable workflows"""
from cg.cli.workflow.base import workflow as workflow_cmd
from cg.models.cg_config import CGConfig
from click.testing import CliRunner

EXIT_SUCCESS = 0


def test_no_options(cli_runner: CliRunner, base_context: CGConfig):
    """Test command with no options"""
    # GIVEN
    # WHEN dry running
    result = cli_runner.invoke(workflow_cmd, obj=base_context)

    # THEN command should have returned all pipelines that is supported
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert "microsalt" in result.output
    assert "mip-dna" in result.output
    assert "mip-rna" in result.output
