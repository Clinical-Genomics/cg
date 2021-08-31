from pathlib import Path

import pytest

from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell
from tests.apps.demultiplex.conftest import fixture_demultiplex_fixtures


@pytest.fixture(name="flowcell_full_name")
def fixture_flowcell_full_name() -> str:
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="flowcell_runs")
def fixture_flowcell_runs(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "flowcell-runs"


@pytest.fixture(name="flowcell_path")
def fixture_flowcell_path(flowcell_runs: Path, flowcell_full_name: str) -> Path:
    return flowcell_runs / flowcell_full_name


@pytest.fixture(name="flowcell_object")
def fixture_flowcell_object(flowcell_path: Path) -> Flowcell:
    return Flowcell(flowcell_path)


@pytest.fixture(name="demultiplexed_runs")
def fixture_demultiplexed_runs(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "demultiplexed-runs"


@pytest.fixture(name="demultiplexed_flowcell")
def fixture_demultiplexed_flowcell(demultiplexed_runs: Path, flowcell_full_name: str) -> Path:
    return demultiplexed_runs / flowcell_full_name


@pytest.fixture(name="bcl2fastq_demux_results")
def fixture_bcl2fastq_demux_results(
    demultiplexed_flowcell: Path, flowcell_object: Flowcell
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_flowcell, flowcell=flowcell_object, bcl_converter="bcl2fastq"
    )


@pytest.fixture(name="dragen_demux_results")
def fixture_dragen_demux_results(
    demultiplexed_flowcell: Path, flowcell_object: Flowcell
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_flowcell, flowcell=flowcell_object, bcl_converter="dragen"
    )
