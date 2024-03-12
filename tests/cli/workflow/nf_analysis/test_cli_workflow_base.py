"""Tests CLI common methods to assess workflow base command for NF analyses."""

from click.testing import CliRunner

from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.constants import Workflow

@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER],#,  Workflow.TOMTE],
)

def test_workflow_no_args(cli_runner: CliRunner, workflow: Workflow ):
    """Test to see that running workflow without options prints help and doesn't result in an error."""
    context = request.getfixturevalue(f"{workflow}_context")
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(workflow, [], obj=context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output
