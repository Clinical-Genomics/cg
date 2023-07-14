"""Test demultiplex API."""
from pathlib import Path
from typing import List

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.cg_config import CGConfig


def test_get_all_demultiplexed_flow_cell_out_dirs(
    demultiplex_context: CGConfig, demultiplexed_flow_cell_finished_working_directory: Path
):
    """Test returning all flow cell directories from the demultiplexing run directory."""
    # GIVEN a demultiplex flow cell finished output directory that exist

    # GIVEN a demultiplex context
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api

    # WHEN calling get_all_demultiplexed_flow_cell_dirs
    demultiplex_flow_cell_dirs: List[Path] = demux_api.get_all_demultiplexed_flow_cell_dirs()

    # THEN the demultiplexed flow cells run directories should be returned
    assert demultiplex_flow_cell_dirs[0] == demultiplexed_flow_cell_finished_working_directory
