from pathlib import Path

from click.testing import CliRunner
from cg.cli.workflow.raredisease.base import panel, managed_variants
from cg.constants.scout import ScoutExportFileName
from cg.io.txt import read_txt
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig


def test_panel_dry_run(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_panel_output: str,
    mocker,
):
    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    mocker.patch.object(RarediseaseAnalysisAPI, "get_gene_panel", return_value=scout_panel_output)

    result = cli_runner.invoke(panel, [raredisease_case_id, "--dry-run"], obj=raredisease_context)
    # THEN the output should contain the output from Scout
    actual_output = "".join(result.stdout.strip().split())
    expected_output = "".join(scout_panel_output.strip().split())

    assert actual_output == expected_output


def test_panel_file_is_written(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_panel_output: str,
    mocker,
):
    # GIVEN an analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    mocker.patch.object(RarediseaseAnalysisAPI, "get_gene_panel", return_value=scout_panel_output)

    cli_runner.invoke(panel, [raredisease_case_id], obj=raredisease_context)

    panel_file = Path(analysis_api.root, raredisease_case_id, ScoutExportFileName.PANELS)

    # THEN the file should exist
    assert panel_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=panel_file, read_to_string=True)
    assert "".join(file_content.strip().split()) == "".join(scout_panel_output.strip().split())


def test_managed_variants_is_written(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_export_manged_variants_output: str,
    mocker,
):
    # GIVEN an analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN a mocked scout export of the managed variants
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_managed_variants",
        return_value=scout_export_manged_variants_output,
    )
    managed_variants_file = Path(
        analysis_api.root, raredisease_case_id, ScoutExportFileName.MANAGED_VARIANTS
    )

    # WHEN creating a managed variants file
    cli_runner.invoke(managed_variants, [raredisease_case_id], obj=raredisease_context)

    # THEN the file should exist
    assert managed_variants_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=managed_variants_file, read_to_string=True)
    assert "".join(file_content.strip().split()) == "".join(
        scout_export_manged_variants_output.strip().split()
    )


def test_managed_variants_dry_run(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_export_manged_variants_output: str,
    mocker,
):
    # GIVEN a case

    # GIVEN a mocked scout export of the managed variants
    mocker.patch.object(
        RarediseaseAnalysisAPI,
        "get_managed_variants",
        return_value=scout_export_manged_variants_output,
    )
    result = cli_runner.invoke(
        managed_variants, [raredisease_case_id, "--dry-run"], obj=raredisease_context
    )

    # THEN the result should contain the output from Scout
    assert "".join(result.stdout.strip().split()) == "".join(
        scout_export_manged_variants_output.strip().split()
    )
