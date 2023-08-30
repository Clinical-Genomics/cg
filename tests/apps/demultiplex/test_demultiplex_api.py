"""Tests for functions of DemultiplexAPI."""

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import add_sample_sheet_path_to_housekeeper
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


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
