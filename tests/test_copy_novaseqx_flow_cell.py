from pathlib import Path
from typing import Set
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import get_latest_analysis_directory

from cg.cli.demultiplex.demux import (
    hardlink_flow_cell_analysis_data,
    is_ready_for_post_processing,
)
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles


def test_flow_cell_is_ready_for_post_processing(
    novaseqx_flow_cell_dir_with_analysis_data: Path, demultiplexed_flow_cell_run_directory: Path
):
    # GIVEN a flow cell which is ready for post processing

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        novaseqx_flow_cell_dir_with_analysis_data, demultiplexed_flow_cell_run_directory
    )

    # THEN the flow cell is ready for post processing
    assert is_flow_cell_ready


def test_flow_cell_is_not_ready_for_post_processing_without_analysis(
    novaseqx_flow_cell_analysis_incomplete: Path, demultiplexed_flow_cell_run_directory: Path
):
    # GIVEN a flow cell for which analysis is not completed

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        novaseqx_flow_cell_analysis_incomplete, demultiplexed_flow_cell_run_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_flow_cell_is_not_ready_for_post_processing_if_not_demultiplexed(
    demultiplex_not_complete_novaseqx_flow_cell: Path, demultiplexed_flow_cell_run_directory: Path
):
    # GIVEN a flow cell for which demultiplexing is not completed

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        demultiplex_not_complete_novaseqx_flow_cell, demultiplexed_flow_cell_run_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_previously_post_processed_flow_cell_is_not_ready(
    post_processed_novaseqx_flow_cell: Path, demultiplexed_flow_cell_run_directory: Path
):
    # GIVEN a flow cell for which post processing is done

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        post_processed_novaseqx_flow_cell, demultiplexed_flow_cell_run_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_previously_copied_flow_cell_is_not_ready(
    novaseqx_flow_cell_dir_with_analysis_data: Path, demultiplexed_flow_cell_run_directory: Path
):
    # GIVEN a flow cell which already exists in demultiplexed runs
    Path(
        demultiplexed_flow_cell_run_directory, novaseqx_flow_cell_dir_with_analysis_data.name
    ).mkdir()

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        novaseqx_flow_cell_dir_with_analysis_data, demultiplexed_flow_cell_run_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_get_latest_analysis_version_path(
    novaseqx_flow_cell_dir_with_analysis_data: Path,
    novaseqx_latest_analysis_version: str,
):
    # GIVEN a flow cell which is ready to be post processed

    # WHEN extracting the latest analysis version path
    analysis_path: Path = get_latest_analysis_directory(novaseqx_flow_cell_dir_with_analysis_data)

    # THEN the latest analysis version path is returned
    latest_analysis_path: Path = Path(
        novaseqx_flow_cell_dir_with_analysis_data,
        DemultiplexingDirsAndFiles.ANALYSIS,
        novaseqx_latest_analysis_version,
    )
    assert analysis_path == latest_analysis_path


def test_copy_novaseqx_flow_cell(
    demultiplexed_flow_cell_run_directory: Path,
    novaseqx_flow_cell_dir_with_analysis_data: Path,
    novaseqx_flow_cell_dir_name: str,
):
    # GIVEN a destination directory
    flow_cell_run = Path(demultiplexed_flow_cell_run_directory, novaseqx_flow_cell_dir_name)
    flow_cell_run.mkdir()
    destination = Path(flow_cell_run, DemultiplexingDirsAndFiles.DATA)

    # WHEN copying the flow cell analysis data to demultiplexed runs
    hardlink_flow_cell_analysis_data(novaseqx_flow_cell_dir_with_analysis_data, destination)

    # THEN the data contains everything from the analysis folder
    analysis: Path = get_latest_analysis_directory(novaseqx_flow_cell_dir_with_analysis_data)
    analysis_data_path: Path = Path(analysis / DemultiplexingDirsAndFiles.DATA)

    original_files = get_all_files(analysis_data_path)
    copied_files = get_all_files(destination)

    assert original_files == copied_files


def get_all_files(base_path: Path) -> Set[Path]:
    """Get a set of all files relative to base_path."""
    return {file.relative_to(base_path) for file in base_path.rglob("*") if file.is_file()}
