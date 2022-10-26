import logging
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig, DemultiplexConfig
from cg.models.demultiplex.flowcell import Flowcell
from cg.utils import Process
from tests.apps.cgstats.conftest import fixture_populated_stats_api, fixture_stats_api
from tests.apps.demultiplex.conftest import (
    fixture_demux_run_dir,
    fixture_demux_run_dir_bcl2fastq,
    fixture_demux_run_dir_dragen,
    fixture_lims_novaseq_bcl2fastq_samples,
    fixture_lims_novaseq_dragen_samples,
    fixture_lims_novaseq_samples,
    fixture_novaseq_dir,
    fixture_novaseq_dir_bcl2fastq,
    fixture_novaseq_dir_dragen,
    fixture_novaseq_run_parameters,
)
from tests.models.demultiplexing.conftest import (
    fixture_bcl2fastq_demux_results,
    fixture_demultiplexed_flowcell,
)

LOG = logging.getLogger(__name__)


@pytest.fixture(name="demux_results_finished_dir")
def fixture_demux_results_finished_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with demultiplexing results where files are renamed etc."""
    return Path(demultiplex_fixtures, "demultiplexed-runs")


@pytest.fixture(name="demux_results_not_finished_dir")
def fixture_demux_results_not_finished_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with demultiplexing results where demux has been done but nothing is cleaned."""
    return Path(demultiplex_fixtures, "demultiplexed-runs-unfinished")


@pytest.fixture(name="flowcell_object")
def fixture_flowcell_object(demux_run_dir: Path, flowcell_full_name: str) -> Flowcell:
    """Create a flow cell object with flow cell that is demultiplexed."""
    return Flowcell(flowcell_path=Path(demux_run_dir, flowcell_full_name))


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_path")
def fixture_novaseq_bcl2fastq_sample_sheet_path(demultiplex_fixtures: Path) -> Path:
    """Return the path to a Novaseq bcl2fastq sample sheet."""
    return Path(demultiplex_fixtures, "SampleSheetS2_Bcl2Fastq.csv")


@pytest.fixture(name="flowcell_runs_working_directory")
def fixture_flowcell_runs_working_directory(project_dir: Path) -> Path:
    """Return the path to a working directory with flow cells ready for demux."""
    working_dir: Path = Path(project_dir, "flowcell-runs")
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="flowcell_runs_working_directory_bcl2fastq")
def fixture_flowcell_runs_working_directory_bcl2fastq(
    flowcell_runs_working_directory: Path,
) -> Path:
    """Return the path to a working directory with flowcells ready for demux."""
    working_dir: Path = Path(flowcell_runs_working_directory, "bcl2fastq")
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="flowcell_runs_working_directory_dragen")
def fixture_flowcell_runs_working_directory_dragen(flowcell_runs_working_directory: Path) -> Path:
    """Return the path to a working directory with flow cells ready for demux."""
    working_dir: Path = Path(flowcell_runs_working_directory, "dragen")
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="demultiplexed_flowcells_working_directory")
def fixture_demultiplexed_flowcells_working_directory(project_dir: Path) -> Path:
    """Return the path to a working directory with flowc  'ells that have been demultiplexed."""
    working_dir: Path = Path(project_dir, "demultiplexed-runs")
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="demultiplexed_flowcell_working_directory")
def fixture_demultiplexed_flowcell_working_directory(
    demux_results_not_finished_dir: Path,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
) -> Path:
    """Copy the content of a demultiplexed but not finished directory to a temporary location."""
    source: Path = Path(demux_results_not_finished_dir, flowcell_full_name)
    destination: Path = Path(demultiplexed_flowcells_working_directory, flowcell_full_name)
    shutil.copytree(src=source, dst=destination)
    return destination


@pytest.fixture(name="demultiplexed_flowcell_finished_working_directory")
def fixture_demultiplexed_flowcell_finished_working_directory(
    demux_results_finished_dir: Path,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
) -> Path:
    """Copy the content of a demultiplexed but not finished directory to a temporary location."""
    source: Path = Path(demux_results_finished_dir, flowcell_full_name)
    destination: Path = Path(demultiplexed_flowcells_working_directory, flowcell_full_name)
    shutil.copytree(src=source, dst=destination)
    return destination


@pytest.fixture(name="flowcell_working_directory")
def fixture_flowcell_working_directory(
    novaseq_dir: Path, flowcell_runs_working_directory: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flowcell directory with the run parameters present.
    """
    working_dir: Path = Path(flowcell_runs_working_directory, novaseq_dir.name)
    working_dir.mkdir(parents=True)
    existing_flowcell: Flowcell = Flowcell(flowcell_path=novaseq_dir)
    working_flowcell: Flowcell = Flowcell(flowcell_path=working_dir)
    shutil.copy(
        existing_flowcell.run_parameters_path.as_posix(),
        working_flowcell.run_parameters_path.as_posix(),
    )
    return working_dir


@pytest.fixture(name="flowcell_working_directory_bcl2fastq")
def fixture_flowcell_working_directory_bcl2fastq(
    flowcell_dir_bcl2fastq: Path, flowcell_runs_working_directory_bcl2fastq: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flowcell directory with the run parameters present.
    """
    working_dir: Path = Path(flowcell_runs_working_directory_bcl2fastq, flowcell_dir_bcl2fastq.name)
    working_dir.mkdir(parents=True)
    existing_flowcell: Flowcell = Flowcell(flowcell_path=flowcell_dir_bcl2fastq)
    working_flowcell: Flowcell = Flowcell(flowcell_path=working_dir)
    shutil.copy(
        existing_flowcell.run_parameters_path.as_posix(),
        working_flowcell.run_parameters_path.as_posix(),
    )
    return working_dir


@pytest.fixture(name="flowcell_working_directory_dragen")
def fixture_flowcell_working_directory_dragen(
    flowcell_dir_dragen: Path, flowcell_runs_working_directory_dragen: Path
) -> Path:
    """Return the path to a working directory that will be deleted after test is run.

    This is a path to a flowcell directory with the run parameters present.
    """
    working_dir: Path = Path(flowcell_runs_working_directory_dragen, flowcell_dir_dragen.name)
    working_dir.mkdir(parents=True)
    existing_flowcell: Flowcell = Flowcell(flowcell_path=flowcell_dir_dragen)
    working_flowcell: Flowcell = Flowcell(flowcell_path=working_dir)
    shutil.copy(
        existing_flowcell.run_parameters_path.as_posix(),
        working_flowcell.run_parameters_path.as_posix(),
    )
    return working_dir


@pytest.fixture(name="flowcell_working_directory_no_run_parameters")
def fixture_flowcell_working_directory_no_run_parameters(
    novaseq_dir: Path, flowcell_runs_working_directory: Path
) -> Path:
    """This is a path to a flow cell directory with the run parameters missing."""
    working_dir: Path = Path(flowcell_runs_working_directory, novaseq_dir.name)
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture(name="demultiplex_ready_flowcell")
def fixture_demultiplex_ready_flowcell(flowcell_working_directory: Path, novaseq_dir: Path) -> Path:
    """Return the path to a working directory that is ready for demultiplexing.

    This is a path to a flowcell directory with all the files necessary to start demultiplexing present.
    """
    existing_flowcell: Flowcell = Flowcell(flowcell_path=novaseq_dir)
    working_flowcell: Flowcell = Flowcell(flowcell_path=flowcell_working_directory)
    shutil.copy(
        existing_flowcell.sample_sheet_path.as_posix(),
        working_flowcell.sample_sheet_path.as_posix(),
    )
    shutil.copy(
        str(DemultiplexingAPI.get_stderr_logfile(existing_flowcell)),
        str(DemultiplexingAPI.get_stderr_logfile(working_flowcell)),
    )
    working_flowcell.copy_complete_path.touch()
    working_flowcell.rta_complete_path.touch()
    return flowcell_working_directory


@pytest.fixture(name="demultiplex_ready_flowcell_bcl2fastq")
def fixture_demultiplex_ready_flowcell_bcl2fastq(
    flowcell_working_directory_bcl2fastq: Path, flowcell_dir_bcl2fastq: Path
) -> Path:
    """Return the path to a working directory that is ready for demultiplexing.

    This is a path to a flow cell directory with all the files necessary to start demultiplexing present.
    """
    existing_flowcell: Flowcell = Flowcell(flowcell_path=flowcell_dir_bcl2fastq)
    working_flowcell: Flowcell = Flowcell(flowcell_path=flowcell_working_directory_bcl2fastq)
    shutil.copy(
        existing_flowcell.sample_sheet_path.as_posix(),
        working_flowcell.sample_sheet_path.as_posix(),
    )
    shutil.copy(
        str(DemultiplexingAPI.get_stderr_logfile(existing_flowcell)),
        str(DemultiplexingAPI.get_stderr_logfile(working_flowcell)),
    )
    working_flowcell.copy_complete_path.touch()
    working_flowcell.rta_complete_path.touch()
    return flowcell_working_directory_bcl2fastq


@pytest.fixture(name="demultiplex_ready_flowcell_dragen")
def fixture_demultiplex_ready_flowcell_dragen(
    flowcell_working_directory_dragen: Path, flowcell_dir_dragen: Path
) -> Path:
    """Return the path to a working directory that is ready for demultiplexing.

    This is a path to a flowcell directory with all the files necessary to start demultiplexing present.
    """
    existing_flowcell: Flowcell = Flowcell(
        flowcell_path=flowcell_dir_dragen, bcl_converter="dragen"
    )
    working_flowcell: Flowcell = Flowcell(
        flowcell_path=flowcell_working_directory_dragen, bcl_converter="dragen"
    )
    shutil.copy(
        existing_flowcell.sample_sheet_path.as_posix(),
        working_flowcell.sample_sheet_path.as_posix(),
    )
    shutil.copy(
        str(DemultiplexingAPI.get_stderr_logfile(existing_flowcell)),
        str(DemultiplexingAPI.get_stderr_logfile(working_flowcell)),
    )
    working_flowcell.copy_complete_path.touch()
    working_flowcell.rta_complete_path.touch()
    return flowcell_working_directory_dragen


@pytest.fixture(name="sample_sheet_context")
def fixture_sample_sheet_context(cg_context: CGConfig, lims_api: LimsAPI) -> CGConfig:
    """Return cg context with an added lims API."""
    cg_context.lims_api_ = lims_api
    return cg_context


@pytest.fixture(name="demultiplex_configs")
def fixture_demultiplex_configs(
    flowcell_runs_working_directory: Path,
    demultiplexed_flowcells_working_directory: Path,
    demultiplex_fixtures: Path,
) -> dict:
    """Return demultiplex configs."""
    demultiplexed_flowcells_working_directory.mkdir(parents=True, exist_ok=True)
    return {
        "demultiplex": {
            "out_dir": demultiplexed_flowcells_working_directory.as_posix(),
            "run_dir": flowcell_runs_working_directory.as_posix(),
            "slurm": {"account": "test", "mail_user": "testuser@github.se"},
        }
    }


@pytest.fixture(name="demultiplexing_api")
def fixture_demultiplexing_api(
    demultiplex_configs: dict, sbatch_process: Process
) -> DemultiplexingAPI:
    """Return demultiplex API."""
    demux_api = DemultiplexingAPI(config=demultiplex_configs)
    demux_api.slurm_api.process = sbatch_process
    return demux_api


@pytest.fixture(name="demultiplex_context")
def fixture_demultiplex_context(
    demultiplexing_api: DemultiplexingAPI,
    stats_api: StatsAPI,
    real_housekeeper_api: HousekeeperAPI,
    cg_context: CGConfig,
) -> CGConfig:
    """Return cg context witha demultiplex context."""
    cg_context.demultiplex_api_ = demultiplexing_api
    cg_context.cg_stats_api_ = stats_api
    cg_context.housekeeper_api_ = real_housekeeper_api
    return cg_context


@pytest.fixture(name="cli_runner")
def fixture_cli_runner():
    """Create a CliRunner"""
    return CliRunner()
