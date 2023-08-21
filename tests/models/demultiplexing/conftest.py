from pathlib import Path

import pytest

from cg.constants.demultiplexing import BclConverter
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


@pytest.fixture(name="demultiplexed_bcl_convert_flow_cell")
def fixture_demultiplexed_bcl_convert_flow_cell(
    demultiplexed_runs: Path, bcl_convert_flow_cell_full_name: str
) -> Path:
    return Path(demultiplexed_runs, bcl_convert_flow_cell_full_name)


@pytest.fixture(name="dragen_demux_results")
def fixture_dragen_demux_results(
    demultiplexed_bcl_convert_flow_cell: Path, bcl_convert_flow_cell: FlowCellDirectoryData
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_bcl_convert_flow_cell,
        flow_cell=bcl_convert_flow_cell,
        bcl_converter=BclConverter.DRAGEN,
    )
