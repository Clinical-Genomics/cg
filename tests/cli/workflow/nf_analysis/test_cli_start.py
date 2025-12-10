from unittest.mock import MagicMock

import pytest
from click import BaseCommand
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.workflow.nallo.base import start as nallo_start
from cg.cli.workflow.raredisease.base import start as raredisease_start
from cg.cli.workflow.rnafusion.base import start as rnafusion_start
from cg.cli.workflow.taxprofiler.base import start as taxprofiler_start
from cg.cli.workflow.tomte.base import start as tomte_start
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter


@pytest.mark.parametrize(
    "start_command",
    [nallo_start, raredisease_start, rnafusion_start, taxprofiler_start, tomte_start],
    ids=["Nallo", "raredisease", "RNAFUSION", "Taxprofiler", "Tomte"],
)
def test_start_nextflow_calls_service(
    start_command: BaseCommand,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a valid context and a case id
    case_id: str = "case_id"

    # GIVEN a mocked AnalysisStarter that simulates the start method
    service_call: MagicMock = mocker.patch.object(AnalysisStarter, "start")

    # WHEN running the start command
    result: Result = cli_runner.invoke(
        start_command, [case_id, "--revision", "revision"], obj=cg_context
    )

    # THEN the analysis started should have been called with the flags set
    service_call.assert_called_once_with(case_id=case_id, revision="revision")

    # THEN the command should have executed without fail
    assert result.exit_code == EXIT_SUCCESS
