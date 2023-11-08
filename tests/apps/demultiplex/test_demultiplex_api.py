"""Tests for functions of DemultiplexAPI."""
from pathlib import Path

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_is_sample_sheet_in_housekeeper_exists(
    demultiplexing_context_for_demux: CGConfig, tmp_bcl2fastq_flow_cell: FlowCellDirectoryData
):
    """Test that checking the existence of an existing sample sheet in Housekeeper returns True."""
    # GIVEN a DemultiplexAPI and a flow cell with a sample sheet
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demultiplexing_context_for_demux.flow_cells_dir = tmp_bcl2fastq_flow_cell.path.parent

    # GIVEN that the sample sheet is in Housekeeper
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl2fastq_flow_cell.path,
        flow_cell_name=tmp_bcl2fastq_flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # WHEN testing if the sample sheet is in Housekeeper
    result: bool = demux_api.is_sample_sheet_in_housekeeper(flow_cell_id=tmp_bcl2fastq_flow_cell.id)

    # THEN the sample sheet should be in Housekeeper
    assert result


def test_is_sample_sheet_in_housekeeper_not_in_hk(
    demultiplexing_context_for_demux: CGConfig, tmp_bcl2fastq_flow_cell: FlowCellDirectoryData
):
    """Test that checking the existence of a non-existing sample sheet in Housekeeper returns False."""
    # GIVEN a DemultiplexAPI and a flow cell with a sample sheet
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demultiplexing_context_for_demux.flow_cells_dir = tmp_bcl2fastq_flow_cell.path.parent

    # GIVEN that the sample sheet is not in Housekeeper

    # WHEN testing if the sample sheet is in Housekeeper
    result: bool = demux_api.is_sample_sheet_in_housekeeper(flow_cell_id=tmp_bcl2fastq_flow_cell.id)

    # THEN the sample sheet should be in Housekeeper
    assert not result


def test_create_demultiplexing_output_dir_for_bcl2fastq(
    tmp_bcl2fastq_flow_cell, tmp_path, demultiplexing_context_for_demux: CGConfig
):
    """Test that the correct demultiplexing output directory is created."""
    # GIVEN a Bcl2Fastq FlowCellDirectoryData object

    # GIVEN that the demultiplexing output directory does not exist
    demux_dir = Path(tmp_path, DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME)
    unaligned_dir = Path(demux_dir, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
    assert not demux_dir.exists()
    assert not unaligned_dir.exists()

    # WHEN creating the demultiplexing output directory for a bcl2fastq flow cell
    demultiplexing_context_for_demux.demultiplex_api.create_demultiplexing_output_dir(
        flow_cell=tmp_bcl2fastq_flow_cell, demux_dir=demux_dir, unaligned_dir=unaligned_dir
    )

    # THEN the demultiplexing output directory should exist
    assert demux_dir.exists()
    assert unaligned_dir.exists()


def test_create_demultiplexing_output_dir_for_bcl_convert(
    tmp_bcl_convert_flow_cell, tmp_path, demultiplexing_context_for_demux: CGConfig
):
    """Test that the correct demultiplexing output directory is created."""
    # GIVEN BCL Convert FlowCellDirectoryData object

    # GIVEN that the demultiplexing output directory does not exist
    demux_dir = Path(tmp_path, DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME)
    unaligned_dir = Path(demux_dir, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
    assert not demux_dir.exists()
    assert not unaligned_dir.exists()

    # WHEN creating the demultiplexing output directory for a BCL Convert flow cell
    demultiplexing_context_for_demux.demultiplex_api.create_demultiplexing_output_dir(
        flow_cell=tmp_bcl_convert_flow_cell, demux_dir=demux_dir, unaligned_dir=unaligned_dir
    )

    # THEN the demultiplexing output directory should exist
    assert demux_dir.exists()
    assert not unaligned_dir.exists()
