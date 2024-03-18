"""Tests CLI common methods to create the case config for NF analyses."""

import logging

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_SUCCESS, Workflow
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_config_case_without_options(
    cli_runner: CliRunner, workflow: Workflow, request: FixtureRequest
):
    """Test config_case for workflow without options."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # WHEN dry running without anything specified
    result = cli_runner.invoke(workflow_cli, [workflow, "config-case"], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_config_case_with_missing_case(
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    workflow: Workflow,
    request: FixtureRequest,
):
    """Test config_case for workflow with a missing case."""
    caplog.set_level(logging.ERROR)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case not in the StatusDB database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running
    result = cli_runner.invoke(
        workflow_cli, [workflow, "config-case", case_id_does_not_exist], obj=context
    )

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN the error log should indicate that the case is invalid
    assert "could not be found in Status DB!" in caplog.text
