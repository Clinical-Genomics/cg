import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.raredisease.base import start, start_available
from cg.cli.workflow.rnafusion.base import start, start_available
from cg.cli.workflow.taxprofiler.base import start, start_available
from cg.constants import EXIT_SUCCESS, Workflow
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI

from cg.models.cg_config import CGConfig
from tests.cli.workflow.conftest import mock_analysis_flow_cell


@pytest.mark.parametrize(
    "workflow,context",
    [
        (
            Workflow.RAREDISEASE,
            Workflow.RAREDISEASE + "_context",
        ),
        (
            Workflow.RNAFUSION,
            Workflow.RNAFUSION + "_context",
        ),
        (
            Workflow.TAXPROFILER,
            Workflow.TAXPROFILER + "_context",
        ),
    ]
)
def test_no_args(cli_runner: CliRunner, context: CGConfig, workflow: str, request):
    """Test to see that running BALSAMIC without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call
    workflow = request.getfixturevalue(workflow)

    # WHEN running command
    result = cli_runner.invoke(workflow, [], obj=context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output


@pytest.mark.parametrize(
    "context,case_id,api",
    [
        (
            Workflow.RAREDISEASE + "_context",
            Workflow.RAREDISEASE + "_case_id",
            Workflow.RAREDISEASE.title() + "AnalysisAPI",
        ),
        (
            Workflow.RNAFUSION + "_context",
            Workflow.RNAFUSION + "_case_id",
            Workflow.RNAFUSION.title() + "AnalysisAPI",
        ),
        (
            Workflow.TAXPROFILER + "_context",
            Workflow.TAXPROFILER + "_case_id",
            Workflow.TAXPROFILER.title() + "AnalysisAPI",
        ),
    ],
)
def test_start(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    case_id: str,
    api: NfAnalysisAPI,
    mock_analysis_flow_cell,
    request,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN case id
    case_id: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    case_id: str = request.getfixturevalue(case_id)

    request.getfixturevalue(api).resolve_decompression.return_value = None

    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text


@pytest.mark.parametrize(
    "context,case_id,api",
    [
        (
            Workflow.RAREDISEASE + "_context",
            Workflow.RAREDISEASE + "_case_id",
            Workflow.RAREDISEASE.title() + "AnalysisAPI",
        ),
        (
            Workflow.RNAFUSION + "_context",
            Workflow.RNAFUSION + "_case_id",
            Workflow.RNAFUSION.title() + "AnalysisAPI",
        ),
        (
            Workflow.TAXPROFILER + "_context",
            Workflow.TAXPROFILER + "_case_id",
            Workflow.TAXPROFILER.title() + "AnalysisAPI",
        ),
    ],
)
def test_start_available_enough_reads(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    case_id: str,
    api: NfAnalysisAPI,
    mock_analysis_flow_cell,
    request,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(request.getfixturevalue(api), "resolve_decompression")
    request.getfixturevalue(api).resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id_success in caplog.text


@pytest.mark.parametrize(
    "context,case_id,api",
    [
        (
            Workflow.RAREDISEASE + "_context",
            Workflow.RAREDISEASE + "_case_id",
            Workflow.RAREDISEASE.title() + "AnalysisAPI",
        ),
        (
            Workflow.RNAFUSION + "_context",
            Workflow.RNAFUSION + "_case_id",
            Workflow.RNAFUSION.title() + "AnalysisAPI",
        ),
        (
            Workflow.TAXPROFILER + "_context",
            Workflow.TAXPROFILER + "_case_id",
            Workflow.TAXPROFILER.title() + "AnalysisAPI",
        ),
    ],
)
def test_start_available_not_enough_reads(
    cli_runner: CliRunner,
    context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    case_id: str,
    api: NfAnalysisAPI,
    case_id_not_enough_reads: str,
    request,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)
    context = request.getfixturevalue(context)

    # GIVEN a case passing read counts threshold and another one not passing
    case_id: str = request.getfixturevalue(case_id)

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(request.getfixturevalue(api), "resolve_decompression")
    request.getfixturevalue(api).resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id in caplog.text

    # THEN the case without enough reads should not start
    assert case_id_not_enough_reads not in caplog.text
