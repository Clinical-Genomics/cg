from pathlib import Path
import pytest

from cg.cli.demultiplex.demux import is_demultiplexed


@pytest.fixture
def demultiplex_complete_novaseqx_flow_cell(tmp_path: Path) -> Path:
    # Create the necessary directories and files
    (tmp_path / "Analysis" / "1").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Analysis" / "1" / "CopyComplete.txt").touch()
    
    (tmp_path / "Analysis" / "1" / "Data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Analysis" / "1" / "Data" / "Secondary_Analysis_Complete.txt").touch()
    
    return tmp_path


@pytest.fixture
def demultiplex_not_complete_novaseqx_flow_cell(tmp_file) -> Path:
    return tmp_file


def test_flow_cell_is_demultiplexed(demultiplex_complete_novaseqx_flow_cell: Path):
    # GIVEN a flow cell for which demultiplexing is completed

    # WHEN checking if the flow cell is demultiplexed
    is_demultiplexing_completed = is_demultiplexed(demultiplex_complete_novaseqx_flow_cell)

    # THEN the flow cell is demultiplexed
    assert is_demultiplexing_completed


def test_flow_cell_is_not_demultiplexed(demultiplex_not_complete_novaseqx_flow_cell: Path):
    # GIVEN a flow cell for which demultiplexing is not completed

    # WHEN checking if the flow cell is demultiplexed
    is_demultiplexing_completed = is_demultiplexed(demultiplex_not_complete_novaseqx_flow_cell)

    # THEN the flow cell is not demultiplexed
    assert not is_demultiplexing_completed
