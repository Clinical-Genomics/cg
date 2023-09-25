import datetime as dt

from click.testing import CliRunner

from cg.cli.workflow.fluffy.base import start_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Sample


def test_start_available_dry(
    cli_runner: CliRunner, fluffy_case_id_existing: str, fluffy_context: CGConfig, caplog
):
    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # WHEN running command with dry-run flag active
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=fluffy_context)

    # THEN log informs about starting full workflow
    assert "Starting full" in caplog.text

    # THEN log informs about process running
    assert "Running command" in caplog.text

    # THEN case_id is mentioned in the log
    assert fluffy_case_id_existing in caplog.text

    # THEN log informs that dry run is active
    assert "Dry run" in caplog.text

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS


def test_start_available(
    cli_runner: CliRunner,
    fluffy_case_id_existing: str,
    fluffy_context: CGConfig,
    caplog,
    mocker,
    sample: Sample,
):
    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # GIVEN successful process execution
    mocker.patch.object(FluffyAnalysisAPI, "run_fluffy")
    FluffyAnalysisAPI.run_fluffy.return_value = None

    # GIVEN Concentrations are set in LIMS on sample level
    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = "20"

    # GIVEN every sample in SampleSheet has been given a name in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    # GIVEN every sample in SampleSheet reads_updated_at set in StatusDB
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_sequenced_date")
    FluffyAnalysisAPI.get_sample_sequenced_date.return_value = dt.datetime.now().date()

    # GIVEN every sample in SampleSheet has control status ""
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_control_status")
    FluffyAnalysisAPI.get_sample_control_status.return_value = False

    # GIVEN a mocked response from status_db.get_sample_by_internal_id
    mocker.patch.object(fluffy_context.status_db, "get_sample_by_internal_id")
    fluffy_context.status_db.get_sample_by_internal_id.return_value = sample

    # WHEN running command
    result = cli_runner.invoke(start_available, [], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs about starting full workflow
    assert "Starting full" in caplog.text

    # THEN case_id eligible to start is mentioned in the log
    assert fluffy_case_id_existing in caplog.text
