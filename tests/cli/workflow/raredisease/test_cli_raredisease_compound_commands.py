import logging

from pathlib import Path
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from mock import mock

from cg.cli.workflow.raredisease.base import managed_variants, panel, start, start_available
from cg.constants import EXIT_SUCCESS
from cg.constants.scout import ScoutExportFileName
from cg.io.txt import read_txt
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.conftest import create_process_response

SUBPROCESS_RUN_FUNCTION_NAME: str = "cg.utils.commands.subprocess.run"


def test_panel_dry_run(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_panel_output: str,
):
    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    with mock.patch(
        SUBPROCESS_RUN_FUNCTION_NAME,
        return_value=create_process_response(std_out=scout_panel_output),
    ):
        # WHEN creating a panel file using dry-run
        result = cli_runner.invoke(
            panel, [raredisease_case_id, "--dry-run"], obj=raredisease_context
        )

    # THEN the output should contain the output from Scout
    assert result.stdout.strip() == scout_panel_output


def test_panel_file_is_written(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_panel_output: str,
):
    # GIVEN an analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    with mock.patch(
        SUBPROCESS_RUN_FUNCTION_NAME,
        return_value=create_process_response(std_out=scout_panel_output),
    ):
        # WHEN creating a panel file
        cli_runner.invoke(panel, [raredisease_case_id], obj=raredisease_context)

    panel_file = Path(analysis_api.root, raredisease_case_id, ScoutExportFileName.PANELS)

    # THEN the file should exist
    assert panel_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=panel_file, read_to_string=True)
    assert file_content == scout_panel_output


def test_managed_variants_is_written(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_export_manged_variants_output: str,
):
    # GIVEN an analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the managed variants to stdout
    with mock.patch(
        SUBPROCESS_RUN_FUNCTION_NAME,
        return_value=create_process_response(std_out=scout_export_manged_variants_output),
    ):
        # WHEN creating a managed_variants file
        cli_runner.invoke(managed_variants, [raredisease_case_id], obj=raredisease_context)

    managed_variants_file = Path(
        analysis_api.root, raredisease_case_id, ScoutExportFileName.MANAGED_VARIANTS
    )

    # THEN the file should exist
    assert managed_variants_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=managed_variants_file, read_to_string=True)
    assert file_content == scout_export_manged_variants_output


def test_managed_variants_dry_run(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_export_manged_variants_output: str,
):
    # GIVEN a case

    # GIVEN that, the Scout command writes the managed variants to stdout
    with mock.patch(
        SUBPROCESS_RUN_FUNCTION_NAME,
        return_value=create_process_response(std_out=scout_export_manged_variants_output),
    ):
        # WHEN creating a managed_variants file using dry run
        result = cli_runner.invoke(
            managed_variants, [raredisease_case_id, "--dry-run"], obj=raredisease_context
        )

    # THEN the result should contain the output from Scout
    assert result.stdout.strip() == scout_export_manged_variants_output


def test_start(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    raredisease_case_id: str,
    mock_analysis_flow_cell,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions."""
    caplog.set_level(logging.INFO)

    # GIVEN case id
    case_id: str = raredisease_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    RarediseaseAnalysisAPI.resolve_decompression.return_value = None

    # WHEN dry running with dry specified
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=raredisease_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text

    # THEN command should not include resume flag
    assert "-resume" not in caplog.text


def test_start_available_enough_reads(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    raredisease_case_id: str,
    mock_analysis_flow_cell,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success: str = raredisease_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(RarediseaseAnalysisAPI, "resolve_decompression")
    RarediseaseAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=raredisease_context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id_success in caplog.text


def test_start_available_not_enough_reads(
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    caplog: LogCaptureFixture,
    mocker,
    raredisease_case_id: str,
    case_id_not_enough_reads: str,
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones."""
    caplog.set_level(logging.INFO)

    # GIVEN a case passing read counts threshold and another one not passing
    case_id: str = raredisease_case_id

    # GIVEN a mocked config

    # GIVEN decompression is not needed
    mocker.patch.object(RarediseaseAnalysisAPI, "resolve_decompression")
    RarediseaseAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=raredisease_context)

    # THEN command exits with 0
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert case_id in caplog.text

    # THEN the case without enough reads should not start
    assert case_id_not_enough_reads not in caplog.text
