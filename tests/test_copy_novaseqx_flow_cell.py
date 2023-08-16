from pathlib import Path
import pytest

from cg.cli.demultiplex.demux import copy_flow_cell_analysis_data, get_latest_analysis_directory, is_ready_for_post_processing


@pytest.fixture
def latest_analysis_version() -> str:
    return "Analysis/2"


@pytest.fixture
def flow_cell_name() -> str:
    return "20230427_LH00188_0001_B223YYCLT3"

@pytest.fixture
def novaseqx_flow_cell(tmp_path: Path, latest_analysis_version: str, flow_cell_name: str) -> Path:
    # Incomplete analysis version
    (tmp_path / flow_cell_name / "Analysis" / "1").mkdir(parents=True, exist_ok=True)

    # Complete analysis version - old
    (tmp_path / flow_cell_name / "Analysis/0").mkdir(parents=True, exist_ok=True)
    (tmp_path / flow_cell_name / "Analysis/0" / "CopyComplete.txt").touch()

    (tmp_path / flow_cell_name / "Analysis/0" / "Data").mkdir(parents=True, exist_ok=True)
    (tmp_path / flow_cell_name / "Analysis/0" / "Data" / "Secondary_Analysis_Complete.txt").touch()

    # Complete analysis version - most recent
    (tmp_path / flow_cell_name / latest_analysis_version).mkdir(parents=True, exist_ok=True)
    (tmp_path / flow_cell_name / latest_analysis_version / "CopyComplete.txt").touch()

    (tmp_path / flow_cell_name / latest_analysis_version / "Data").mkdir(parents=True, exist_ok=True)
    (tmp_path / flow_cell_name / latest_analysis_version / "Data" / "Secondary_Analysis_Complete.txt").touch()

    return tmp_path


@pytest.fixture
def post_processed_novaseqx_flow_cell(novaseqx_flow_cell) -> Path:
    (novaseqx_flow_cell / "PostProcessed.txt").touch()
    return novaseqx_flow_cell


@pytest.fixture
def novaseqx_flow_cell_analysis_incomplete(tmp_path: Path) -> Path:
    (tmp_path / "Analysis" / "2").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Analysis" / "2" / "CopyComplete.txt").touch()
    return tmp_path


@pytest.fixture
def demultiplex_not_complete_novaseqx_flow_cell(tmp_file) -> Path:
    return tmp_file


def test_flow_cell_is_ready_for_post_processing(novaseqx_flow_cell: Path):
    # GIVEN a flow cell which is ready for post processing

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(novaseqx_flow_cell)

    # THEN the flow cell is ready
    assert ready


def test_is_not_ready_without_analysis(novaseqx_flow_cell_analysis_incomplete: Path):
    # GIVEN a flow cell for which analysis is not completed

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(novaseqx_flow_cell_analysis_incomplete)

    # THEN it is not ready
    assert not ready


def test_flow_cell_is_not_demultiplexed(demultiplex_not_complete_novaseqx_flow_cell: Path):
    # GIVEN a flow cell for which demultiplexing is not completed

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(demultiplex_not_complete_novaseqx_flow_cell)

    # THEN it is not ready
    assert not ready


def test_previously_post_processed_flow_cell_is_not_ready(post_processed_novaseqx_flow_cell: Path):
    # GIVEN a flow cell for which post processing is done

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(post_processed_novaseqx_flow_cell)

    # THEN the flow cell is not ready
    assert not ready


def test_get_latest_analysis_version_path(
    novaseqx_flow_cell: Path, latest_analysis_version: str,
):
    # GIVEN a flow cell which is ready to be post processed

    # WHEN extracting the latest analysis version path
    analysis_directory = get_latest_analysis_directory(novaseqx_flow_cell)

    # THEN the latest analysis version path is returned
    assert analysis_directory == novaseqx_flow_cell / latest_analysis_version


def test_copy_novaseqx_flow_cell(tmp_path: Path, novaseqx_flow_cell: Path, flow_cell_name: str):
    # GIVEN a destination directory
    demultiplexed_runs_directory = tmp_path

    # WHEN copying the flow cell analysis data to demultiplexed runs
    copy_flow_cell_analysis_data(novaseqx_flow_cell, demultiplexed_runs_directory)

    # THEN the flow cell analysis data is copied
    assert (demultiplexed_runs_directory / flow_cell_name).exists()
