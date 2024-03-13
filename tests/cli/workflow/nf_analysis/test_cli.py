import pytest
from enum import Enum
from click.testing import CliRunner
from cg.cli.workflow.raredisease.base import raredisease
from cg.cli.workflow.taxprofiler.base import taxprofiler
from cg.cli.workflow.rnafusion.base import rnafusion

from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig

@pytest.mark.parametrize(
    "pipeline, context",
    [
        (rnafusion, "rnafusion_context"),
        (taxprofiler, "taxprofiler_context"),
        (raredisease, "raredisease_context"),
    ]
)

def test_workflow_no_args(
        cli_runner: CliRunner,
        pipeline,
        context: CGConfig,
        request
):
    """Test to assess that Nextflow workflows without options successfully print help and exist without error."""
    context = request.getfixturevalue(context)

    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(pipeline, [], obj=context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output