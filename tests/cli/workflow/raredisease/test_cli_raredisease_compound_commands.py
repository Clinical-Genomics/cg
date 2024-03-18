from pathlib import Path

from click.testing import CliRunner
from mock import mock

from cg.cli.workflow.raredisease.base import managed_variants, panel
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
