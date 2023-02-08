from cg.cli.workflow.fluffy.base import create_samplesheet
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
import datetime as dt


def test_create_samplesheet_dry(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    fluffy_context: CGConfig,
    caplog,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]
    # GIVEN a case_id that does exist in database

    # WHEN running command to create samplesheet with dry-run flag
    result = cli_runner.invoke(
        create_samplesheet, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context
    )

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN logging informs of the original samplesheet path and destination samplesheet path
    assert "Writing modified csv" in caplog.text

    # THEN no file is created
    assert not fluffy_analysis_api.get_sample_sheet_path(fluffy_case_id_existing).exists()


def test_create_samplesheet_dry_no_case(
    cli_runner: CliRunner,
    fluffy_case_id_non_existing,
    fluffy_context: CGConfig,
    caplog,
):
    caplog.set_level("ERROR")
    # GIVEN a case_id that does not exist in database

    # WHEN running command in dry-run mode and the case_id as argument
    result = cli_runner.invoke(
        create_samplesheet, [fluffy_case_id_non_existing, "--dry-run"], obj=fluffy_context
    )
    # THEN command does NOT terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN logging informs about the case_id not existing
    assert fluffy_case_id_non_existing in caplog.text
    assert "could not be found" in caplog.text


def test_create_samplesheet_success(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    fluffy_context: CGConfig,
    samplesheet_fixture_path,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]
    # GIVEN a case_id that does exist in database

    # GIVEN an existing samplesheet in Housekeeper
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_sheet_housekeeper_path")
    FluffyAnalysisAPI.get_sample_sheet_housekeeper_path.return_value = samplesheet_fixture_path

    # GIVEN Concentrations are set in LIMS on sample level
    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = "20"

    # GIVEN every sample in SampleSheet has been given a name in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    # GIVEN every sample in SampleSheet has valid order field in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_starlims_id")
    FluffyAnalysisAPI.get_sample_starlims_id.return_value = 12345678

    # GIVEN every sample in SampleSheet sequenced_at set in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_sequenced_date")
    FluffyAnalysisAPI.get_sample_sequenced_date.return_value = dt.datetime.now().date()

    # GIVEN every sample in SampleSheet has control status ""
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_control_status")
    FluffyAnalysisAPI.get_sample_control_status.return_value = False

    # WHEN running command to create samplesheet
    result = cli_runner.invoke(create_samplesheet, [fluffy_case_id_existing], obj=fluffy_context)
    # THEN log text is output
    assert "Writing modified csv" in caplog.text

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN newly generated SampleSheet file can be found on disk
    assert fluffy_analysis_api.get_sample_sheet_path(fluffy_case_id_existing).exists()
