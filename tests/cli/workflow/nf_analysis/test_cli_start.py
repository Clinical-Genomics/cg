import logging
from typing import Callable
from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from click import BaseCommand
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.apps.lims import LimsAPI
from cg.cli.workflow.base import workflow as workflow_cli
from cg.cli.workflow.raredisease.base import dev_start as raredisease_start
from cg.cli.workflow.raredisease.base import dev_start_available as raredisease_start_available
from cg.cli.workflow.rnafusion.base import start as rnafusion_start
from cg.cli.workflow.rnafusion.base import start_available as rnafusion_start_available
from cg.cli.workflow.taxprofiler.base import dev_start as taxprofiler_start
from cg.cli.workflow.taxprofiler.base import dev_start_available as taxprofiler_start_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Workflow
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.service import AnalysisStarter


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.TAXPROFILER, Workflow.TOMTE, Workflow.NALLO],
)
def test_start(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    mock_analysis_illumina_run,
    request: FixtureRequest,
    scout_export_manged_variants_output: str,
    mocker,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case id
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked scout export of the managed variants
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_managed_variants",
        return_value=scout_export_manged_variants_output,
    )

    # GIVEN decompression is not needed
    mocker.patch.object(NfAnalysisAPI, "resolve_decompression", return_value=None)

    # GIVEN that the sample source in LIMS is set
    mocker.patch.object(LimsAPI, "get_source", return_value="blood")

    # WHEN invoking the command with dry-run specified
    result = cli_runner.invoke(workflow_cli, [workflow, "start", case_id, "--dry-run"], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.TAXPROFILER, Workflow.TOMTE, Workflow.NALLO],
)
def test_start_available(
    cli_runner: CliRunner,
    workflow: Workflow,
    caplog: LogCaptureFixture,
    mocker,
    mock_analysis_illumina_run,
    request: FixtureRequest,
    case_id_not_enough_reads: str,
    scout_export_manged_variants_output: str,
):
    """
    Test to ensure all parts of compound start-available command are executed given ideal conditions.
    Test that start-available picks up eligible cases and does not pick up ineligible ones.
    """
    caplog.set_level(logging.DEBUG)
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    # GIVEN a case with enough reads and another case with insufficient reads
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(NfAnalysisAPI, "resolve_decompression", return_value=None)

    # GIVEN that the sample source in LIMS is set
    mocker.patch.object(LimsAPI, "get_source", return_value="blood")

    # GIVEN a mocked scout export of the managed variants
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_managed_variants",
        return_value=scout_export_manged_variants_output,
    )

    # WHEN invoking the command with dry-run specified
    result = cli_runner.invoke(
        workflow_cli, [workflow, "start-available", "--dry-run"], obj=context
    )

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id in caplog.text

    # THEN the case without enough reads should not start
    assert case_id_not_enough_reads not in caplog.text


@pytest.mark.parametrize(
    "start_command",
    [raredisease_start, rnafusion_start, taxprofiler_start],
    ids=["raredisease", "RNAFUSION", "Taxprofiler"],
)
def test_start_nextflow_calls_service(
    start_command: Callable,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    # GIVEN a valid context and a case id
    case_id: str = "case_id"

    # GIVEN a mocked AnalysisStarter that simulates the start method
    service_call: MagicMock = mocker.patch.object(AnalysisStarter, "start")

    # WHEN running the start command
    result: Result = cli_runner.invoke(start_command, [case_id], obj=cg_context)

    # THEN the analysis started should have been called with the flags set
    service_call.assert_called_once_with(case_id=case_id)

    # THEN the command should have executed without fail
    assert result.exit_code == EXIT_SUCCESS


@pytest.mark.parametrize(
    "start_available_command",
    [raredisease_start_available, rnafusion_start_available, taxprofiler_start_available],
    ids=["raredisease", "RNAFUSION", "Taxprofiler"],
)
@pytest.mark.parametrize(
    "succeeds, exit_status",
    [
        (True, EXIT_SUCCESS),
        (False, EXIT_FAIL),
    ],
)
def test_start_available_nextflow_calls_service(
    start_available_command: BaseCommand,
    succeeds: bool,
    exit_status: int,
    cli_runner: CliRunner,
    cg_context: CGConfig,
    mocker: MockerFixture,
):
    """
    Test that the start_available command succeeds when the starter succeeds and aborts otherwise.
    """
    # GIVEN a sufficient context

    # GIVEN a mocked AnalysisStarter that simulates the start_available method
    service_call: MagicMock = mocker.patch.object(
        AnalysisStarter, "start_available", return_value=succeeds
    )

    # WHEN running the start-available command
    result: Result = cli_runner.invoke(start_available_command, obj=cg_context)

    # THEN the analysis starter should have been called with the expected input
    service_call.assert_called_once()

    # THEN the command should have executed without fail
    assert result.exit_code == exit_status
