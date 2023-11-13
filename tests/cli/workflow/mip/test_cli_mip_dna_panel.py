""" Test the CLI for mip-dna panel"""
import logging
from pathlib import Path

import mock
from click.testing import CliRunner

from cg.cli.workflow.mip_dna.base import panel
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.conftest import create_process_response

LOG = logging.getLogger(__name__)


def test_panel_file_is_written(
    case_id: str, cli_runner: CliRunner, mip_dna_context: CGConfig, scout_panel_output: str
):
    analysis_api: MipAnalysisAPI = mip_dna_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that the scout command writes the panel to stdout
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(std_out=scout_panel_output),
    ):
        # WHEN creating a panel file
        cli_runner.invoke(panel, [case_id], obj=mip_dna_context)

    panel_file = Path(analysis_api.root, case_id, "gene_panels.bed")

    # THEN the file should exist
    assert panel_file.exists()

    # THEN the file should contain the output from scout
    with open(panel_file, "r") as file_handle:
        assert file_handle.read() == scout_panel_output
