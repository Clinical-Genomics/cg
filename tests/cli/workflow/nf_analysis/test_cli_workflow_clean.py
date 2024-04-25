import logging

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.base import workflow as workflow_cli
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Workflow
from cg.constants.constants import CaseActions
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig


@pytest.mark.parametrize(
    "workflow",
    [Workflow.TAXPROFILER],
)
def test_cli_workflow_clean(
    cli_runner: CliRunner, workflow: Workflow, before_date: str, request: FixtureRequest
):
    """Test clean nf-workflows."""
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    # GIVEN a before string

    # WHEN running command
    result = cli_runner.invoke(workflow_cli, [workflow, "clean", before_date], obj=context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS
