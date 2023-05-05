from pathlib import Path

import pytest

from cg.constants.demultiplexing import BclConverter
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCell


@pytest.fixture(name="flow_cell_name")
def fixture_flow_cell_name(flow_cell_full_name: str) -> str:
    return flow_cell_full_name.split("_")[-1][1:]


@pytest.fixture(name="flow_cell")
def fixture_flow_cell(bcl2fastq_flow_cell_dir: Path) -> FlowCell:
    flow_cell = FlowCell(flow_cell_path=bcl2fastq_flow_cell_dir)
    flow_cell.parse_flow_cell_name()
    return FlowCell(flow_cell_path=bcl2fastq_flow_cell_dir)


@pytest.fixture(name="dragen_flow_cell_full_name")
def fixture_dragen_flow_cell_full_name() -> str:
    return "211101_A00187_0615_AHLG5GDRXY"


@pytest.fixture(name="dragen_flow_cell_path")
def fixture_dragen_flow_cell_path(demux_run_dir: Path, dragen_flow_cell_full_name: str) -> Path:
    return Path(demux_run_dir, dragen_flow_cell_full_name)


@pytest.fixture(name="demultiplexed_dragen_flow_cell")
def fixture_demultiplexed_dragen_flow_cell(
    demultiplexed_runs: Path, dragen_flow_cell_full_name: str
) -> Path:
    return Path(demultiplexed_runs, dragen_flow_cell_full_name)


@pytest.fixture(name="dragen_demux_results")
def fixture_dragen_demux_results(
    demultiplexed_dragen_flow_cell: Path, dragen_flow_cell: FlowCell
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_dragen_flow_cell,
        flow_cell=dragen_flow_cell,
        bcl_converter=BclConverter.DRAGEN,
    )
