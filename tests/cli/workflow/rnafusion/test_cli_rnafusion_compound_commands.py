import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.cli.workflow.rnafusion.base import start, start_available, store_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig


def test_start(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    mock_analysis_flow_cell,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)

    # GIVEN case id
    case_id: str = rnafusion_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    RnafusionAnalysisAPI.resolve_decompression.return_value = None

    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=rnafusion_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text


def test_start_available(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    rnafusion_case_id: str,
    mock_analysis_flow_cell,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success: str = rnafusion_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(RnafusionAnalysisAPI, "resolve_decompression")
    RnafusionAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=rnafusion_context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id_success in caplog.text


def test_start_available(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    rnafusion_case_id: str,
    case_id_not_enough_reads: str,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN a case passing read counts threshold and another one not passing

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(RnafusionAnalysisAPI, "resolve_decompression")
    RnafusionAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=rnafusion_context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert rnafusion_case_id in caplog.text

    # THEN the case without enough reads should not start
    assert case_id_not_enough_reads not in caplog.text
