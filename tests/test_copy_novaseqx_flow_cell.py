from pathlib import Path
import pytest
from typing import Set

from cg.cli.demultiplex.demux import (
    copy_flow_cell_analysis_data,
    get_latest_analysis_directory,
    is_ready_for_post_processing,
)
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles


@pytest.fixture
def latest_analysis_version() -> str:
    return "2"


@pytest.fixture
def flow_cell_name() -> str:
    return "20230427_LH00188_0001_B223YYCLT3"


@pytest.fixture
def flow_cell_directory(tmp_path: Path, flow_cell_name: str) -> Path:
    return tmp_path / flow_cell_name


@pytest.fixture
def demultiplexed_runs(tmp_path: Path) -> Path:
    demultiplexed_runs = Path(tmp_path, "demultiplexed_runs")
    demultiplexed_runs.mkdir()
    return demultiplexed_runs


def add_analysis_data(flow_cell_directory: Path, analysis_version: str):
    analysis_path = Path(flow_cell_directory, DemultiplexingDirsAndFiles.ANALYSIS, analysis_version)
    analysis_path.mkdir(parents=True)
    analysis_path.joinpath(DemultiplexingDirsAndFiles.COPY_COMPLETE).touch()
    data_path = analysis_path.joinpath(DemultiplexingDirsAndFiles.DATA)
    data_path.mkdir()
    data_path.joinpath(DemultiplexingDirsAndFiles.ANALYSIS_COMPLETED).touch()
    return analysis_path


@pytest.fixture
def novaseqx_flow_cell(flow_cell_directory: Path, latest_analysis_version: str) -> Path:
    add_analysis_data(flow_cell_directory, "0")
    add_analysis_data(flow_cell_directory, "1")
    add_analysis_data(flow_cell_directory, latest_analysis_version)
    return flow_cell_directory


@pytest.fixture
def post_processed_novaseqx_flow_cell(novaseqx_flow_cell: Path) -> Path:
    Path(novaseqx_flow_cell, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).touch()
    return novaseqx_flow_cell


@pytest.fixture
def novaseqx_flow_cell_analysis_incomplete(
    flow_cell_directory: Path, latest_analysis_version: str
) -> Path:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.ANALYSIS, latest_analysis_version).mkdir(
        parents=True
    )
    Path(
        flow_cell_directory,
        DemultiplexingDirsAndFiles.ANALYSIS,
        latest_analysis_version,
        DemultiplexingDirsAndFiles.COPY_COMPLETE,
    ).touch()
    return flow_cell_directory


@pytest.fixture
def demultiplex_not_complete_novaseqx_flow_cell(tmp_file: Path) -> Path:
    return tmp_file


def test_flow_cell_is_ready_for_post_processing(novaseqx_flow_cell: Path, demultiplexed_runs: Path):
    # GIVEN a flow cell which is ready for post processing

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(novaseqx_flow_cell, demultiplexed_runs)

    # THEN the flow cell is ready
    assert ready


def test_is_not_ready_without_analysis(
    novaseqx_flow_cell_analysis_incomplete: Path, demultiplexed_runs: Path
):
    # GIVEN a flow cell for which analysis is not completed

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(novaseqx_flow_cell_analysis_incomplete, demultiplexed_runs)

    # THEN it is not ready
    assert not ready


def test_flow_cell_is_not_demultiplexed(
    demultiplex_not_complete_novaseqx_flow_cell: Path, demultiplexed_runs: Path
):
    # GIVEN a flow cell for which demultiplexing is not completed

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(
        demultiplex_not_complete_novaseqx_flow_cell, demultiplexed_runs
    )

    # THEN it is not ready
    assert not ready


def test_previously_post_processed_flow_cell_is_not_ready(
    post_processed_novaseqx_flow_cell: Path, demultiplexed_runs: Path
):
    # GIVEN a flow cell for which post processing is done

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(post_processed_novaseqx_flow_cell, demultiplexed_runs)

    # THEN the flow cell is not ready
    assert not ready


def test_previously_copied_flow_cell_is_not_ready(
    novaseqx_flow_cell: Path, demultiplexed_runs: Path
):
    # GIVEN a flow cell which already exists in demultiplexed runs
    Path(demultiplexed_runs, novaseqx_flow_cell.name).mkdir()

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(novaseqx_flow_cell, demultiplexed_runs)

    # THEN the flow cell is not ready
    assert not ready


def test_get_latest_analysis_version_path(
    novaseqx_flow_cell: Path,
    latest_analysis_version: str,
):
    # GIVEN a flow cell which is ready to be post processed

    # WHEN extracting the latest analysis version path
    analysis = get_latest_analysis_directory(novaseqx_flow_cell)

    # THEN the latest analysis version path is returned
    latest_analysis = Path(
        novaseqx_flow_cell, DemultiplexingDirsAndFiles.ANALYSIS, latest_analysis_version
    )
    assert analysis == latest_analysis


def test_copy_novaseqx_flow_cell(
    demultiplexed_runs: Path, novaseqx_flow_cell: Path, flow_cell_name: str
):
    # GIVEN a destination directory
    flow_cell_run = Path(demultiplexed_runs, flow_cell_name)
    flow_cell_run.mkdir()
    destination = Path(flow_cell_run, DemultiplexingDirsAndFiles.DATA)

    # WHEN copying the flow cell analysis data to demultiplexed runs
    copy_flow_cell_analysis_data(novaseqx_flow_cell, destination)

    # THEN the data contains everything from the analysis folder
    analysis = get_latest_analysis_directory(novaseqx_flow_cell)
    analysis_data = analysis / DemultiplexingDirsAndFiles.DATA

    original_files = get_all_files(analysis_data)
    copied_files = get_all_files(destination)

    assert original_files == copied_files


def get_all_files(base_path: Path) -> Set[Path]:
    """Get a set of all files relative to base_path."""
    return {file.relative_to(base_path) for file in base_path.rglob("*") if file.is_file()}
