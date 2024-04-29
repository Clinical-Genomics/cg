"""Tests CLI common methods to assess workflow base command for NF analyses."""

import pytest
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.constants.nextflow import NEXTFLOW_WORKFLOWS


@pytest.mark.parametrize(
    "workflow",
    NEXTFLOW_WORKFLOWS + [Workflow.JASEN],
)
def test_workflow_no_args(cli_runner: CliRunner, workflow: Workflow, request):
    """Test to see that workflow is added and prints help when no subcommand is specified."""
    context = request.getfixturevalue(f"{workflow}_context")
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(workflow_cli, [workflow], obj=context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output
