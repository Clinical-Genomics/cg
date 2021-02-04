from cg.cli.workflow.fluffy.base import start_available
from cg.constants import EXIT_SUCCESS
from cg.meta.workflow.fluffy import FluffyAnalysisAPI


def test_start_available_dry(cli_runner, fluffy_case_id_existing, fluffy_context, caplog):

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
    cli_runner, fluffy_case_id_existing, fluffy_context, caplog, mocker, samplesheet_fixture_path
):
    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # GIVEN successful process execution
    mocker.patch.object(FluffyAnalysisAPI, "run_fluffy")
    FluffyAnalysisAPI.run_fluffy.return_value = None

    # GIVEN samplesheet exists in Housekeeper
    mocker.patch.object(FluffyAnalysisAPI, "get_samplesheet_housekeeper_path")
    FluffyAnalysisAPI.get_samplesheet_housekeeper_path.return_value = samplesheet_fixture_path

    # GIVEN concentrations on samples are set in LIMS
    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = "10"

    # GIVEN samples in samplesheet have corresponding StatusDB entries with customer-set sample name
    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    # WHEN running command
    result = cli_runner.invoke(start_available, [], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs about starting full workflow
    assert "Starting full" in caplog.text

    # THEN case_id eligible to start is mentioned in the log
    assert fluffy_case_id_existing in caplog.text
