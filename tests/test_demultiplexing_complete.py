
from pathlib import Path
import pytest

from cg.cli.demultiplex.demux import is_demultiplexed


@pytest.fixture
def demultiplex_complete_flow_cell(tmp_file) -> Path:
    return tmp_file


def test_flow_cell_is_demultiplexed(demultiplex_complete_flow_cell: Path):
    # GIVEN a flow cell for which demultiplexing is completed

    # WHEN checking if the flow cell is demultiplexed
    is_demultiplexing_completed = is_demultiplexed(demultiplex_complete_flow_cell)

    # THEN the flow cell is demultiplexed
    assert is_demultiplexing_completed
