from pathlib import Path
import pytest

from cg.cli.demultiplex.demux import get_latest_analysis_directory, is_ready_for_post_processing


@pytest.fixture
def latest_analysis_version() -> str:
    return "Analysis/2"


@pytest.fixture
def demultiplexed_novaseqx_flow_cell(tmp_path: Path, latest_analysis_version: str) -> Path:
    # Incomplete analysis version
    (tmp_path / "Analysis" / "1").mkdir(parents=True, exist_ok=True)

    # Complete analysis version
    (tmp_path / latest_analysis_version).mkdir(parents=True, exist_ok=True)
    (tmp_path / latest_analysis_version / "CopyComplete.txt").touch()

    (tmp_path / latest_analysis_version / "Data").mkdir(parents=True, exist_ok=True)
    (tmp_path / latest_analysis_version / "Data" / "Secondary_Analysis_Complete.txt").touch()

    return tmp_path


@pytest.fixture
def post_processed_novaseqx_flow_cell(demultiplexed_novaseqx_flow_cell) -> Path:
    (demultiplexed_novaseqx_flow_cell / "PostProcessed.txt").touch()
    return demultiplexed_novaseqx_flow_cell


@pytest.fixture
def novaseqx_flow_cell_analysis_incomplete(tmp_path: Path) -> Path:
    (tmp_path / "Analysis" / "2").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Analysis" / "2" / "CopyComplete.txt").touch()
    return tmp_path


@pytest.fixture
def demultiplex_not_complete_novaseqx_flow_cell(tmp_file) -> Path:
    return tmp_file


def test_flow_cell_is_ready_for_post_processing(demultiplexed_novaseqx_flow_cell: Path):
    # GIVEN a flow cell for which demultiplexing is completed

    # WHEN checking if the flow cell is ready for post processing
    ready = is_ready_for_post_processing(demultiplexed_novaseqx_flow_cell)

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
    demultiplexed_novaseqx_flow_cell: Path, latest_analysis_version: str
):
    # GIVEN a flow cell which is ready to be post processed

    # WHEN extracting the latest analysis version path
    analysis_directory = get_latest_analysis_directory(demultiplexed_novaseqx_flow_cell)

    # THEN the latest analysis version path is returned
    assert analysis_directory == demultiplexed_novaseqx_flow_cell / latest_analysis_version
