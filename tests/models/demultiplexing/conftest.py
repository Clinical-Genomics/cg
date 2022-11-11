from pathlib import Path

import pytest

from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCell


@pytest.fixture(name="flow_cell_name")
def fixture_flow_cell_name(flow_cell_full_name: str) -> str:
    return flow_cell_full_name.split("_")[-1][1:]


@pytest.fixture(name="flowcell_runs")
def fixture_flowcell_runs(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "flowcell-runs"


@pytest.fixture(name="flow_cell_full_name")
def fixture_flow_cell_full_name() -> str:
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="flow_cell_path")
def fixture_flowcell_path(flowcell_runs: Path, flow_cell_full_name: str) -> Path:
    return flowcell_runs / flow_cell_full_name


@pytest.fixture(name="flow_cell")
def fixture_flow_cell(flow_cell_path: Path) -> FlowCell:
    flow_cell = FlowCell(flow_cell_path)
    flow_cell.parse_flow_cell_name()
    return FlowCell(flow_cell_path)


@pytest.fixture(name="demultiplexed_flow_cell")
def fixture_demultiplexed_flow_cell(demultiplexed_runs: Path, flow_cell_full_name: str) -> Path:
    return demultiplexed_runs / flow_cell_full_name


@pytest.fixture(name="bcl2fastq_demux_results")
def fixture_bcl2fastq_demux_results(
    demultiplexed_flow_cell: Path, flow_cell: FlowCell
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_flow_cell, flow_cell=flow_cell, bcl_converter="bcl2fastq"
    )


@pytest.fixture(name="dragen_flow_cell_full_name")
def fixture_dragen_flow_cell_full_name() -> str:
    return "211101_A00187_0615_AHLG5GDRXY"


@pytest.fixture(name="dragen_flow_cell_path")
def fixture_dragen_flow_cell_path(flowcell_runs: Path, dragen_flow_cell_full_name: str) -> Path:
    return flowcell_runs / dragen_flow_cell_full_name


@pytest.fixture(name="demultiplexed_dragen_flow_cell")
def fixture_demultiplexed_dragen_flow_cell(
    demultiplexed_runs: Path, dragen_flow_cell_full_name: str
) -> Path:
    return demultiplexed_runs / dragen_flow_cell_full_name


@pytest.fixture(name="dragen_flow_cell")
def fixture_dragen_flow_cell(dragen_flow_cell_path: Path) -> FlowCell:
    flow_cell = FlowCell(dragen_flow_cell_path)
    flow_cell.parse_flow_cell_name()
    return FlowCell(dragen_flow_cell_path)


@pytest.fixture(name="dragen_demux_results")
def fixture_dragen_demux_results(
    demultiplexed_dragen_flow_cell: Path, dragen_flow_cell: FlowCell
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_dragen_flow_cell,
        flow_cell=dragen_flow_cell,
        bcl_converter="dragen",
    )
