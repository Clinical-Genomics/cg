from pathlib import Path

from click.testing import CliRunner
from cg.cli.workflow.nallo.base import panel
from cg.constants.scout import ScoutExportFileName
from cg.io.txt import read_txt
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig


def test_panel_dry_run(
    nallo_case_id: str,
    cli_runner: CliRunner,
    nallo_context: CGConfig,
    scout_panel_output: str,
    mocker,
):
    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    mocker.patch.object(NalloAnalysisAPI, "get_gene_panel", return_value=scout_panel_output)

    result = cli_runner.invoke(panel, [nallo_case_id, "--dry-run"], obj=nallo_context)
    # THEN the output should contain the output from Scout
    actual_output = "".join(result.stdout.strip().split())
    expected_output = "".join(scout_panel_output.strip().split())

    assert actual_output == expected_output


def test_panel_file_is_written(
    nallo_case_id: str,
    cli_runner: CliRunner,
    nallo_context: CGConfig,
    scout_panel_output: str,
    mocker,
):
    # GIVEN an analysis API
    analysis_api: NalloAnalysisAPI = nallo_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    mocker.patch.object(NalloAnalysisAPI, "get_gene_panel", return_value=scout_panel_output)

    cli_runner.invoke(panel, [nallo_case_id], obj=nallo_context)

    panel_file = Path(analysis_api.root, nallo_case_id, ScoutExportFileName.PANELS_TSV)

    # THEN the file should exist
    assert panel_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=panel_file, read_to_string=True)
    assert "".join(file_content.strip().split()) == "".join(scout_panel_output.strip().split())
