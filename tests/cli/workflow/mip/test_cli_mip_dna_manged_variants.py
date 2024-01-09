from pathlib import Path

from click.testing import CliRunner
from mock import mock

from cg.cli.workflow.mip.base import managed_variants
from cg.constants.scout import ScoutExportFileName
from cg.io.txt import read_txt
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.conftest import create_process_response


def test_managed_variants_is_written(
    case_id: str,
    cli_runner: CliRunner,
    mip_dna_context: CGConfig,
    scout_export_manged_variants_output: str,
):
    # GIVEN an analysis API
    analysis_api: MipAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the managed variants to stdout
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(std_out=scout_export_manged_variants_output),
    ):
        # WHEN creating a managed_variants file
        cli_runner.invoke(managed_variants, [case_id], obj=mip_dna_context)

    managed_variants_file = Path(analysis_api.root, case_id, ScoutExportFileName.MANAGED_VARIANTS)

    # THEN the file should exist
    assert managed_variants_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=managed_variants_file, read_to_string=True)
    assert file_content == scout_export_manged_variants_output


def test_managed_variants_dry_run(
    case_id: str,
    cli_runner: CliRunner,
    mip_dna_context: CGConfig,
    scout_export_manged_variants_output: str,
):
    # GIVEN a case

    # GIVEN that, the Scout command writes the managed variants to stdout
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(std_out=scout_export_manged_variants_output),
    ):
        # WHEN creating a managed_variants file using dry run
        result = cli_runner.invoke(managed_variants, [case_id, "--dry-run"], obj=mip_dna_context)

    # THEN the result should contain the output from Scout
    assert result.stdout.strip() == scout_export_manged_variants_output
