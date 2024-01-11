from pathlib import Path

import pytest


@pytest.fixture
def demultiplexed_bcl_convert_flow_cell(
    illumina_novaseq_demultiplexed_runs, bcl_convert_flow_cell_full_name: str
) -> Path:
    return Path(illumina_novaseq_demultiplexed_runs, bcl_convert_flow_cell_full_name)
