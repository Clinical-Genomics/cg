"""Test demultiplex API."""
from pathlib import Path
from typing import List

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.cg_config import CGConfig

from tests.apps.cgstats.conftest import fixture_populated_stats_api, fixture_stats_api
from tests.cli.demultiplex.conftest import (
    fixture_demux_results_finished_dir,
    fixture_demultiplexing_api,
    fixture_demultiplex_configs,
    fixture_flowcell_runs_working_directory,
    fixture_demultiplexed_flowcells_working_directory,
    fixture_demultiplex_context,
    fixture_demultiplexed_flowcell_finished_working_directory,
)


def test_get_all_demultiplex_flow_cells_out_dirs(
    demultiplex_context: CGConfig, demultiplexed_flowcell_finished_working_directory: Path
):
    """Test returning all flow cell directories from demultiplexing."""
    # GIVEN a demultiplex flow cell finished out dir that exist

    # GIVEN that a demultiplex context
    demux_api: DemultiplexingAPI = demultiplex_context.demultiplex_api

    # WHEN calling get_all_demultiplex_flow_cells_out_dirs
    demultiplex_flow_cell_dirs: List[Path] = demux_api.get_all_demultiplex_flow_cells_out_dirs()

    # THEN the demultiplexed flow cells run directories should be returned
    assert demultiplex_flow_cell_dirs[0] == demultiplexed_flowcell_finished_working_directory
