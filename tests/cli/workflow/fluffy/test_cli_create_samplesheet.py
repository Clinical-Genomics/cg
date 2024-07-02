import datetime as dt

from click.testing import CliRunner

from cg.cli.workflow.fluffy.base import create_samplesheet
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import IlluminaSequencingRun, Sample


def test_create_samplesheet_dry(
    cli_runner: CliRunner,
    fluffy_case_id_existing,
    fluffy_context: CGConfig,
    caplog,
):
    caplog.set_level("INFO")

    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]
    # GIVEN a case_id that does exist in database

    # WHEN running command to create sample sheet with dry-run flag
    result = cli_runner.invoke(
        create_samplesheet, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context
    )

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

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
    fluffy_case_id_existing: str,
    fluffy_context: CGConfig,
    sample: Sample,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]
    # GIVEN a case_id that does exist in database

    # GIVEN Concentrations are set in LIMS on sample level
    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = "20"

    # GIVEN every sample in SampleSheet has been given a name in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    # GIVEN every sample in SampleSheet sequenced_at set in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_sequenced_date")
    FluffyAnalysisAPI.get_sample_sequenced_date.return_value = dt.datetime.now().date()

    # GIVEN every sample in SampleSheet has control status ""
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_control_status")
    FluffyAnalysisAPI.get_sample_control_status.return_value = False

    # GIVEN every sample in SampleSheet can be retrieved from status db

    # GIVEN a mocked response from status_db.get_sample_by_internal_id
    mocker.patch.object(fluffy_context.status_db, "get_sample_by_internal_id")
    fluffy_context.status_db.get_sample_by_internal_id.return_value = sample

    # WHEN running command to create samplesheet
    result = cli_runner.invoke(create_samplesheet, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN newly generated SampleSheet file can be found on disk
    assert fluffy_analysis_api.get_sample_sheet_path(fluffy_case_id_existing).exists()


def test_create_fluffy_samplesheet_from_bcl_convert_sample_sheet(
    cli_runner: CliRunner,
    fluffy_case_id_existing: str,
    fluffy_context: CGConfig,
    sample: Sample,
    caplog,
    mocker,
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context.meta_apis["analysis_api"]
    # GIVEN a case_id that does exist in database

    # GIVEN the flow cell for the case was sequenced on a novaseqx machine
    sequencing_run: IlluminaSequencingRun = (
        fluffy_context.status_db.get_latest_illumina_sequencing_run_for_nipt_case(
            fluffy_case_id_existing
        )
    )
    sequencing_run.sequencer_type = "novaseqx"

    # GIVEN Concentrations are set in LIMS on sample level
    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = "20"

    # GIVEN every sample in SampleSheet has been given a name in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    # GIVEN every sample in SampleSheet last_sequenced_at set in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_sequenced_date")
    FluffyAnalysisAPI.get_sample_sequenced_date.return_value = dt.datetime.now().date()

    # GIVEN every sample in SampleSheet has control status ""
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_control_status")
    FluffyAnalysisAPI.get_sample_control_status.return_value = False

    # GIVEN a mocked response from status_db.get_sample_by_internal_id
    mocker.patch.object(fluffy_context.status_db, "get_sample_by_internal_id")
    fluffy_context.status_db.get_sample_by_internal_id.return_value = sample

    # WHEN running command to create samplesheet
    result = cli_runner.invoke(create_samplesheet, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN newly generated SampleSheet file can be found on disk
    assert fluffy_analysis_api.get_sample_sheet_path(fluffy_case_id_existing).exists()
