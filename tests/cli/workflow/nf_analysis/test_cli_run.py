"""This script tests the run cli command"""

import pytest
from click import BaseCommand
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.workflow.nallo.base import run as nallo_run
from cg.cli.workflow.raredisease.base import run as raredisease_run
from cg.cli.workflow.rnafusion.base import run as rnafusion_run
from cg.cli.workflow.taxprofiler.base import run as taxprofiler_run
from cg.cli.workflow.tomte.base import run as tomte_run
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter


@pytest.mark.parametrize(
    "run_command",
    [nallo_run, raredisease_run, rnafusion_run, taxprofiler_run, tomte_run],
    ids=["Nallo", "raredisease", "RNAFUSION", "Taxprofiler", "Tomte"],
)
def test_run_nextflow_calls_service_default_flag_values(
    run_command: BaseCommand,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a case id
    case_id: str = "case_id"

    # WHEN the dev run command is run without flags
    service_call = mocker.patch.object(AnalysisStarter, "run")
    cli_runner.invoke(run_command, [case_id], obj=cg_context)

    # THEN the analysis starter should have been called with the default flag values
    service_call.assert_called_once_with(case_id=case_id, resume=True, revision=None)


@pytest.mark.parametrize(
    "run_command",
    [nallo_run, raredisease_run, rnafusion_run, taxprofiler_run, tomte_run],
    ids=["Nallo", "raredisease", "RNAFUSION", "Taxprofiler", "Tomte"],
)
def test_run_nextflow_calls_service_all_flags_set(
    run_command: BaseCommand,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a case id
    case_id: str = "case_id"

    # WHEN the dev run command is run with all flags set
    service_call = mocker.patch.object(AnalysisStarter, "run")
    cli_runner.invoke(
        run_command, [case_id, "--resume", "false", "--revision", "some_revision"], obj=cg_context
    )

    # THEN the analysis starter should have been called with the flags set
    service_call.assert_called_once_with(case_id=case_id, resume=False, revision="some_revision")
