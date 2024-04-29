"""Tests for running the demultiplex flowcell command"""

import logging
from pathlib import Path

from click import testing

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flow_cell
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_demultiplex_dragen_flowcell(
    cli_runner: testing.CliRunner,
    tmp_flow_cell_directory_bcl_convert: Path,
    demultiplexing_context_for_demux: CGConfig,
    caplog,
    mocker,
):
    caplog.set_level(logging.INFO)

    # GIVEN that all files are present for Dragen demultiplexing

    flow_cell = FlowCellDirectoryData(tmp_flow_cell_directory_bcl_convert)
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_flow_cell_directory_bcl_convert,
        flow_cell_name=flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # GIVEN a flow cell that is ready for demultiplexing
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demux_dir: Path = demux_api.flow_cell_out_dir_path(flow_cell)
    assert demux_api.is_demultiplexing_possible(flow_cell=flow_cell)
    mocker.patch("cg.apps.tb.TrailblazerAPI.add_pending_analysis")

    # GIVEN an already existing output directory
    demux_dir.mkdir(parents=True)
    marker_file = Path(demux_dir, "dummy_file_present_in_old_dir")
    marker_file.touch()
    assert marker_file.exists()

    # WHEN starting demultiplexing from the CLI
    result: testing.Result = cli_runner.invoke(
        demultiplex_flow_cell,
        [str(tmp_flow_cell_directory_bcl_convert)],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0

    # THEN assert the results folder was created
    assert demux_dir.exists()

    # THEN assert that the old directory was removed
    assert not marker_file.exists()

    # THEN assert that the sbatch script was created
    assert demux_api.demultiplex_sbatch_path(flow_cell).exists()


def test_demultiplex_all_novaseq(
    cli_runner: testing.CliRunner,
    demultiplexing_context_for_demux: CGConfig,
    tmp_illumina_flow_cells_demux_all_directory,
    caplog,
):
    """Test the demultiplex-all command on a directory with newly sequenced NovaSeq6000 flow cells."""
    caplog.set_level(logging.INFO)

    # GIVEN a demultiplexing context with an API and correct structure
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    assert demux_api.flow_cells_dir == tmp_illumina_flow_cells_demux_all_directory

    # GIVEN sequenced flow cells with their sample sheet in Housekeeper
    for flow_cell_dir in tmp_illumina_flow_cells_demux_all_directory.iterdir():
        flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(flow_cell_path=flow_cell_dir)
        add_and_include_sample_sheet_path_to_housekeeper(
            flow_cell_directory=flow_cell_dir,
            flow_cell_name=flow_cell.id,
            hk_api=demultiplexing_context_for_demux.housekeeper_api,
        )
        assert demultiplexing_context_for_demux.housekeeper_api.last_version(bundle=flow_cell.id)

    # WHEN running the demultiplex all command
    result: testing.Result = cli_runner.invoke(
        demultiplex_all,
        ["--flow-cells-directory", str(demux_api.flow_cells_dir), "--dry-run"],
        obj=demultiplexing_context_for_demux,
    )

    # THEN assert it exits without problems
    assert result.exit_code == 0

    # THEN assert it found the directory
    assert "Found directory" in caplog.text

    # THEN assert it found a flow cell that is ready for demultiplexing
    assert f"Flow cell {flow_cell.id} is ready for downstream processing" in caplog.text


def test_is_demultiplexing_complete(tmp_novaseq_6000_pre_1_5_kits_flow_cell_path: Path):
    """Tests the is_demultiplexing_complete property of FlowCellDirectoryData."""

    # GIVEN a demultiplexing directory with no demuxcomplete.txt file
    flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
        flow_cell_path=tmp_novaseq_6000_pre_1_5_kits_flow_cell_path
    )
    assert not flow_cell.is_demultiplexing_complete

    # WHEN creating the demuxcomplete.txt file
    Path(flow_cell.path, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()

    # THEN the property should return true
    assert flow_cell.is_demultiplexing_complete
