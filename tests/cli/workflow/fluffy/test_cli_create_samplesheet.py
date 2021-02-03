import random
from pathlib import Path

from cg.cli.workflow.fluffy.base import create_samplesheet
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.meta.workflow.fluffy import FluffyAnalysisAPI


def test_create_samplesheet_dry(
    cli_runner,
    fluffy_case_id_existing,
    fluffy_context,
    caplog,
):
    caplog.set_level("INFO")
    result = cli_runner.invoke(
        create_samplesheet, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context
    )
    assert result.exit_code == EXIT_SUCCESS
    assert "Writing modified csv" in caplog.text


def test_create_samplesheet_success(
    cli_runner, fluffy_case_id_existing, fluffy_context, samplesheet_fixture_path, caplog, mocker
):
    caplog.set_level("INFO")
    fluffy_analysis_api: FluffyAnalysisAPI = fluffy_context["fluffy_analysis_api"]
    Path(fluffy_analysis_api.root_dir, fluffy_case_id_existing).mkdir(parents=True, exist_ok=True)

    mocker.patch.object(FluffyAnalysisAPI, "get_samplesheet_housekeeper_path")
    FluffyAnalysisAPI.get_samplesheet_housekeeper_path.return_value = samplesheet_fixture_path

    mocker.patch.object(FluffyAnalysisAPI, "get_concentrations_from_lims")
    FluffyAnalysisAPI.get_concentrations_from_lims.return_value = str(random.randint(1, 20))

    mocker.patch.object(FluffyAnalysisAPI, "get_sample_name_from_lims_id")
    FluffyAnalysisAPI.get_sample_name_from_lims_id.return_value = "CustName"

    result = cli_runner.invoke(create_samplesheet, [fluffy_case_id_existing], obj=fluffy_context)
    assert "Writing modified csv" in caplog.text
    assert result.exit_code == EXIT_SUCCESS
    assert fluffy_analysis_api.get_samplesheet_path(fluffy_case_id_existing).exists()
