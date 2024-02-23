""" Test the CLI for mip-dna panel"""

from pathlib import Path

import mock
from click.testing import CliRunner

from cg.cli.workflow.mip_dna.base import panel
from cg.constants.scout import ScoutExportFileName
from cg.io.txt import read_txt
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.conftest import create_process_response


def test_panel_file_is_written(
    case_id: str, cli_runner: CliRunner, mip_dna_context: CGConfig, scout_panel_output: str
):
    # GIVEN an analysis API
    analysis_api: MipAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(std_out=scout_panel_output),
    ):
        # WHEN creating a panel file
        cli_runner.invoke(panel, [case_id], obj=mip_dna_context)

    panel_file = Path(analysis_api.root, case_id, ScoutExportFileName.PANELS)

    # THEN the file should exist
    assert panel_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=panel_file, read_to_string=True)
    assert file_content == scout_panel_output
