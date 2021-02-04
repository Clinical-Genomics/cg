from cg.cli.workflow.fluffy.base import start_available
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.meta.workflow.fluffy import FluffyAnalysisAPI


def test_start_available_dry(cli_runner, fluffy_case_id_existing, fluffy_context, caplog):
    caplog.set_level("INFO")
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=fluffy_context)
    assert "Starting full" in caplog.text
    assert "Running command" in caplog.text
    assert fluffy_case_id_existing in caplog.text
    assert result.exit_code == EXIT_SUCCESS


def test_start_available(
    cli_runner, fluffy_case_id_existing, fluffy_context, caplog, mocker, samplesheet_fixture_path
):
    caplog.set_level("INFO")

    mocker.patch.object(FluffyAnalysisAPI, "run_fluffy")
    FluffyAnalysisAPI.run_fluffy.return_value = None

    mocker.patch.object(FluffyAnalysisAPI, "get_samplesheet_housekeeper_path")
    FluffyAnalysisAPI.get_samplesheet_housekeeper_path.return_value = samplesheet_fixture_path

    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = "10"

    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    result = cli_runner.invoke(start_available, [], obj=fluffy_context)
    assert result.exit_code == EXIT_SUCCESS
    assert "Starting full" in caplog.text
    assert fluffy_case_id_existing in caplog.text
