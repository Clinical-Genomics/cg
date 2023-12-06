"""Tests for functions of DemultiplexAPI."""
from pathlib import Path

import pytest

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


def test_is_demultiplexing_possible_true(
    demultiplexing_api: DemultiplexingAPI,
    tmp_bcl_convert_flow_cell: FlowCellDirectoryData,
):
    """Test demultiplexing pre-check when all criteria are fulfilled."""
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_api.hk_api,
    )
    # GIVEN a flow cell with no missing file

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        flow_cell=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell is ready for demultiplexing
    assert result is True


@pytest.mark.parametrize("missing_file", ["RTAComplete.txt", "CopyComplete.txt", "SampleSheet.csv"])
def test_is_demultiplexing_possible_missing_files(
    demultiplexing_api: DemultiplexingAPI,
    missing_file: str,
    tmp_bcl_convert_flow_cell: FlowCellDirectoryData,
):
    """Test demultiplexing pre-check when files are missing in flow cell directory."""
    # GIVEN a flow cell with a samplesheet in Housekeeper
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_api.hk_api,
    )

    # GIVEN that all other demultiplexing criteria are fulfilled
    assert (
        demultiplexing_api.is_demultiplexing_possible(flow_cell=tmp_bcl_convert_flow_cell) is True
    )

    # GIVEN a flow cell with a missing file
    Path(tmp_bcl_convert_flow_cell.path, missing_file).unlink()

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        flow_cell=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell should not be deemed ready for demultiplexing
    assert result is False


def is_demultiplexing_possible_no_sample_sheet_in_hk(
    demultiplexing_api: DemultiplexingAPI,
    tmp_bcl_convert_flow_cell: FlowCellDirectoryData,
):
    """Test demultiplexing pre-check when no samplesheet exists in housekeeper."""
    # GIVEN a flow cell with no sample sheet in Housekeeper
    assert (
        demultiplexing_api.is_sample_sheet_in_housekeeper(flow_cell_id=tmp_bcl_convert_flow_cell.id)
        is False
    )

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        flow_cell=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell should not be deemed ready for demultiplexing
    assert result is False


def test_is_demultiplexing_possible_already_started(
    demultiplexing_api: DemultiplexingAPI,
    tmp_bcl_convert_flow_cell: FlowCellDirectoryData,
):
    """Test demultiplexing pre-check demultiplexing has already started."""
    # GIVEN a flow cell with a sample sheet in Housekeeper
    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_api.hk_api,
    )
    # GIVEN that all other demultiplexing criteria are fulfilled
    assert (
        demultiplexing_api.is_demultiplexing_possible(flow_cell=tmp_bcl_convert_flow_cell) is True
    )

    # GIVEN a flow cell where demultiplexing has already started
    Path(tmp_bcl_convert_flow_cell.path, DemultiplexingDirsAndFiles.DEMUX_STARTED).touch()

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        flow_cell=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell should not be deemed ready for demultiplexing
    assert result is False


def test_remove_demultiplexing_output_directory(
    demultiplexing_api: DemultiplexingAPI,
    tmp_path: Path,
    bcl_convert_flow_cell: FlowCellDirectoryData,
):
    """Test that the demultiplexing output directory is removed."""
    # GIVEN a flow cell with a demultiplexing output directory
    demultiplexing_api.demultiplexed_runs_dir = tmp_path
    demultiplexing_api.create_demultiplexing_output_dir(
        flow_cell=bcl_convert_flow_cell,
        demux_dir=Path(tmp_path, bcl_convert_flow_cell.full_name),
        unaligned_dir=None,
    )
    assert demultiplexing_api.flow_cell_out_dir_path(bcl_convert_flow_cell).exists()

    # WHEN removing the demultiplexing output directory
    demultiplexing_api.remove_demultiplexing_output_directory(flow_cell=bcl_convert_flow_cell)

    assert not demultiplexing_api.flow_cell_out_dir_path(bcl_convert_flow_cell).exists()
