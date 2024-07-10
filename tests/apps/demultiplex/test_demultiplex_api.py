"""Tests for functions of DemultiplexAPI."""

from pathlib import Path

import pytest

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.utils import add_and_include_sample_sheet_path_to_housekeeper
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


def test_is_sample_sheet_in_housekeeper_exists(
    demultiplexing_context_for_demux: CGConfig, tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData
):
    """Test that checking the existence of an existing sample sheet in Housekeeper returns True."""
    # GIVEN a DemultiplexAPI and a flow cell with a sample sheet
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demultiplexing_context_for_demux.run_instruments.illumina.sequencing_runs_dir = (
        tmp_bcl_convert_flow_cell.path.parent
    )

    # GIVEN that the sample sheet is in Housekeeper
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_context_for_demux.housekeeper_api,
    )

    # WHEN testing if the sample sheet is in Housekeeper
    result: bool = demux_api.is_sample_sheet_in_housekeeper(
        flow_cell_id=tmp_bcl_convert_flow_cell.id
    )

    # THEN the sample sheet should be in Housekeeper
    assert result


def test_is_sample_sheet_in_housekeeper_not_in_hk(
    demultiplexing_context_for_demux: CGConfig, tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData
):
    """Test that checking the existence of a non-existing sample sheet in Housekeeper returns False."""
    # GIVEN a DemultiplexAPI and a flow cell with a sample sheet
    demux_api: DemultiplexingAPI = demultiplexing_context_for_demux.demultiplex_api
    demultiplexing_context_for_demux.run_instruments.illumina.sequencing_runs_dir = (
        tmp_bcl_convert_flow_cell.path.parent
    )

    # GIVEN that the sample sheet is not in Housekeeper

    # WHEN testing if the sample sheet is in Housekeeper
    result: bool = demux_api.is_sample_sheet_in_housekeeper(
        flow_cell_id=tmp_bcl_convert_flow_cell.id
    )

    # THEN the sample sheet should be in Housekeeper
    assert not result


def test_create_demultiplexing_output_dir_for_bcl_convert(
    tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData,
    tmp_path: Path,
    demultiplexing_api: DemultiplexingAPI,
):
    """Test that the correct demultiplexing output directory is created."""
    # GIVEN BCL Convert FlowCellDirectoryData object

    # GIVEN that the demultiplexing output directory does not exist
    demultiplexing_api.demultiplexed_runs_dir = tmp_path
    output_directory: Path = demultiplexing_api.demultiplexed_run_dir_path(
        tmp_bcl_convert_flow_cell
    )
    unaligned_directory: Path = demultiplexing_api.get_sequencing_run_unaligned_dir(
        tmp_bcl_convert_flow_cell
    )
    assert not output_directory.exists()
    assert not unaligned_directory.exists()

    # WHEN creating the demultiplexing output directory for a BCL Convert flow cell
    demultiplexing_api.create_demultiplexing_output_dir(tmp_bcl_convert_flow_cell)

    # THEN the demultiplexing output directory should exist
    assert output_directory.exists()
    assert not unaligned_directory.exists()


def test_is_demultiplexing_possible_true(
    demultiplexing_api: DemultiplexingAPI,
    tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData,
):
    """Test demultiplexing pre-check when all criteria are fulfilled."""
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_api.hk_api,
    )
    # GIVEN a flow cell with no missing file

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        sequencing_run=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell is ready for demultiplexing
    assert result is True


@pytest.mark.parametrize("missing_file", ["RTAComplete.txt", "CopyComplete.txt", "SampleSheet.csv"])
def test_is_demultiplexing_possible_missing_files(
    demultiplexing_api: DemultiplexingAPI,
    missing_file: str,
    tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData,
):
    """Test demultiplexing pre-check when files are missing in flow cell directory."""
    # GIVEN a flow cell with a sample sheet in Housekeeper
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_api.hk_api,
    )

    # GIVEN that all other demultiplexing criteria are fulfilled
    assert (
        demultiplexing_api.is_demultiplexing_possible(sequencing_run=tmp_bcl_convert_flow_cell)
        is True
    )

    # GIVEN a flow cell with a missing file
    Path(tmp_bcl_convert_flow_cell.path, missing_file).unlink()

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        sequencing_run=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell should not be deemed ready for demultiplexing
    assert result is False


def is_demultiplexing_possible_no_sample_sheet_in_hk(
    demultiplexing_api: DemultiplexingAPI,
    tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData,
):
    """Test demultiplexing pre-check when no sample sheet exists in Housekeeper."""
    # GIVEN a flow cell with no sample sheet in Housekeeper
    assert (
        demultiplexing_api.is_sample_sheet_in_housekeeper(flow_cell_id=tmp_bcl_convert_flow_cell.id)
        is False
    )

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        sequencing_run=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell should not be deemed ready for demultiplexing
    assert result is False


def test_is_demultiplexing_possible_already_started(
    demultiplexing_api: DemultiplexingAPI,
    tmp_bcl_convert_flow_cell: IlluminaRunDirectoryData,
):
    """Test demultiplexing pre-check demultiplexing has already started."""
    # GIVEN a flow cell with a sample sheet in Housekeeper
    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=tmp_bcl_convert_flow_cell.path,
        flow_cell_name=tmp_bcl_convert_flow_cell.id,
        hk_api=demultiplexing_api.hk_api,
    )
    # GIVEN that all other demultiplexing criteria are fulfilled
    assert (
        demultiplexing_api.is_demultiplexing_possible(sequencing_run=tmp_bcl_convert_flow_cell)
        is True
    )

    # GIVEN a flow cell where demultiplexing has already started
    Path(tmp_bcl_convert_flow_cell.path, DemultiplexingDirsAndFiles.DEMUX_STARTED).touch()

    # WHEN checking if demultiplexing is possible
    result: bool = demultiplexing_api.is_demultiplexing_possible(
        sequencing_run=tmp_bcl_convert_flow_cell
    )
    # THEN the flow cell should not be deemed ready for demultiplexing
    assert result is False


def test_remove_demultiplexing_output_directory(
    demultiplexing_api: DemultiplexingAPI,
    tmp_path: Path,
    novaseq_6000_post_1_5_kits_flow_cell: IlluminaRunDirectoryData,
):
    """Test that the demultiplexing output directory is removed."""
    # GIVEN a flow cell with a demultiplexing output directory
    demultiplexing_api.demultiplexed_runs_dir = tmp_path
    demultiplexing_api.create_demultiplexing_output_dir(novaseq_6000_post_1_5_kits_flow_cell)
    assert demultiplexing_api.demultiplexed_run_dir_path(
        novaseq_6000_post_1_5_kits_flow_cell
    ).exists()

    # WHEN removing the demultiplexing output directory
    demultiplexing_api.remove_demultiplexing_output_directory(
        sequencing_run=novaseq_6000_post_1_5_kits_flow_cell
    )

    assert not demultiplexing_api.demultiplexed_run_dir_path(
        novaseq_6000_post_1_5_kits_flow_cell
    ).exists()
