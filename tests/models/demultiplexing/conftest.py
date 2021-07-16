from pathlib import Path
from typing import Dict

import pytest

from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell
from tests.apps.demultiplex.conftest import *


@pytest.fixture(name="flowcell_full_name")
def fixture_flowcell_full_name() -> str:
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="flowcell_runs")
def fixture_flowcell_runs(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "flowcell_runs"


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


@pytest.fixture(name="bcl2fastq_flowcell_object")
def fixture_bcl2fastq_flowcell_object(bcl2fastq_flowcell_dir: Path) -> Flowcell:
    return Flowcell(bcl2fastq_flowcell_dir)


@pytest.fixture(name="bcl2fastq_demux_results")
def fixture_bcl2fastq_demux_results(
    demultiplexed_flowcell: Path,
    bcl2fastq_flowcell_object: Flowcell,
    bcl2fastq_demux_stats_files: Dict,
) -> DemuxResults:
    return DemuxResults(
        demux_dir=demultiplexed_flowcell,
        flowcell=bcl2fastq_flowcell_object,
        bcl_converter="bcl2fastq",
        demux_stats_files=bcl2fastq_demux_stats_files,
    )


@pytest.fixture(name="finished_dragen_demux_dir")
def fixture_finish_dragen_demux_dir(finished_demuxes_dir: Path) -> Path:
    """returns the path to all finished bcl2fastq demux fixtures"""
    return finished_demuxes_dir / "dragen"


@pytest.fixture(name="dragen_demux_outdir")
def fixture_dragen_demux_outdir(finished_dragen_demux_dir: Path) -> Path:
    """return the path to a finished demultiplexed run (dragen)"""
    return finished_dragen_demux_dir / "210428_A00689_0260_BHNC2FDSXY"


@pytest.fixture(name="dragen_unaligned_dir")
def fixture_dragen_unaligned_dir(finished_dragen_demux_dir: Path) -> Path:
    """return the path to a bcl2fastq unaligned dir"""
    return finished_dragen_demux_dir / "Unaligned"


@pytest.fixture(name="dragen_reports_dir")
def fixture_dragen_reports_dir(dragen_unaligned_dir: Path) -> Path:
    """return the path to a Dragen Reports dir"""
    return dragen_unaligned_dir / "Reports"


@pytest.fixture(name="dragen_adapter_metrics")
def fixture_dragen_adapter_metrics(dragen_reports_dir: Path) -> Path:
    """return the path to the adapter metrics file"""
    return dragen_reports_dir / "Adapter_Metrics.csv"


@pytest.fixture(name="dragen_demultiplex_stats")
def fixture_dragen_demultiplex_stats(dragen_reports_dir: Path) -> Path:
    """return the path to the demultiplex stats file"""
    return dragen_reports_dir / "Demultiplex_Stats.csv"


@pytest.fixture(name="dragen_run_info")
def fixture_dragen_run_info(dragen_reports_dir: Path) -> Path:
    """return the path to the run info file"""
    return dragen_reports_dir / "RunInfo.xml"


@pytest.fixture(name="dragen_demux_stats_files")
def fixture_dragen_demux_stats_files(
    dragen_adapter_metrics: Path, dragen_demultiplex_stats: Path, dragen_run_info: Path
) -> Dict:
    """return a fixture for dragen demux_stats_files"""
    return {
        "conversion_stats": dragen_adapter_metrics,
        "demultiplexing_stats": dragen_demultiplex_stats,
        "runinfo": dragen_run_info,
    }


@pytest.fixture(name="dragen_demux_results")
def fixture_dragen_demux_results(
    bcl2fastq_demux_outdir: Path,
    flowcell_object: Flowcell,
    # dragen_demux_stats_files: Dict
) -> DemuxResults:
    return DemuxResults(
        demux_dir=bcl2fastq_demux_outdir,
        flowcell=flowcell_object,
        bcl_converter="dragen",
        # demux_stats_files=dragen_demux_stats_files,
    )
