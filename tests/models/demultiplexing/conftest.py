from pathlib import Path

import pytest


@pytest.fixture
def demultiplexed_bcl_convert_flow_cell(
    illumina_demultiplexed_runs_directory: Path, bcl_convert_flow_cell_full_name: str
) -> Path:
    return Path(illumina_demultiplexed_runs_directory, bcl_convert_flow_cell_full_name)
