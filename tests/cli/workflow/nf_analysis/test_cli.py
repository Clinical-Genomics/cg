"""Tests CLI common methods that Nextflow workflows print help and exits without error."""

import pytest
from _pytest.fixtures import FixtureRequest
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.models.cg_config import CGConfig


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_workflow_no_args(cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest):
    """Test to assess that Nextflow workflows without options successfully print help and exits without error."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(workflow_cli, [], obj=context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output
