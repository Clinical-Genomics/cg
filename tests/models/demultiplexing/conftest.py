from pathlib import Path

import pytest

from cg.constants.demultiplexing import BclConverter

from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


@pytest.fixture(name="demultiplexed_dragen_flow_cell")
def fixture_demultiplexed_dragen_flow_cell(
    demultiplexed_runs: Path, dragen_flow_cell_full_name: str
) -> Path:
    return Path(demultiplexed_runs, dragen_flow_cell_full_name)
