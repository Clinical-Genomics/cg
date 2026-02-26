from pathlib import Path

from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import get_latest_analysis_path
from cg.cli.demultiplex.demux import is_ready_for_post_processing
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles


def test_flow_cell_is_ready_for_post_processing(
    novaseqx_flow_cell_dir_with_analysis_data: Path,
    tmp_illumina_demultiplexed_runs_directory: Path,
):
    # GIVEN a flow cell which is ready for post processing

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        novaseqx_flow_cell_dir_with_analysis_data, tmp_illumina_demultiplexed_runs_directory
    )

    # THEN the flow cell is ready for post processing
    assert is_flow_cell_ready


def test_flow_cell_is_not_ready_for_post_processing_without_analysis(
    novaseqx_flow_cell_analysis_incomplete: Path, tmp_illumina_demultiplexed_runs_directory: Path
):
    # GIVEN a flow cell for which analysis is not completed

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        novaseqx_flow_cell_analysis_incomplete, tmp_illumina_demultiplexed_runs_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_flow_cell_is_not_ready_for_post_processing_when_not_demultiplexed(
    demultiplex_not_complete_novaseqx_flow_cell: Path,
    tmp_illumina_demultiplexed_runs_directory: Path,
):
    # GIVEN a flow cell for which demultiplexing is not completed

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        demultiplex_not_complete_novaseqx_flow_cell, tmp_illumina_demultiplexed_runs_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_previously_copied_flow_cell_is_not_ready(
    novaseqx_flow_cell_dir_with_analysis_data: Path,
    tmp_illumina_demultiplexed_runs_directory: Path,
):
    # GIVEN a flow cell which already exists in demultiplexed runs
    Path(
        tmp_illumina_demultiplexed_runs_directory, novaseqx_flow_cell_dir_with_analysis_data.name
    ).mkdir()

    # WHEN checking if the flow cell is ready for post processing
    is_flow_cell_ready: bool = is_ready_for_post_processing(
        novaseqx_flow_cell_dir_with_analysis_data, tmp_illumina_demultiplexed_runs_directory
    )

    # THEN the flow cell is not ready for post processing
    assert not is_flow_cell_ready


def test_get_latest_analysis_version_path(
    novaseqx_flow_cell_dir_with_analysis_data: Path,
    novaseqx_latest_analysis_version: str,
):
    # GIVEN a flow cell which is ready to be post processed

    # WHEN extracting the latest analysis version path
    analysis_path: Path = get_latest_analysis_path(novaseqx_flow_cell_dir_with_analysis_data)

    # THEN the latest analysis version path is returned
    latest_analysis_path: Path = Path(
        novaseqx_flow_cell_dir_with_analysis_data,
        DemultiplexingDirsAndFiles.ANALYSIS,
        novaseqx_latest_analysis_version,
    )
    assert analysis_path == latest_analysis_path
