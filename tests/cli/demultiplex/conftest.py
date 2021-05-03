import shutil
from pathlib import Path

import pytest
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig, DemultiplexConfig
from cg.models.demultiplex.flowcell import Flowcell
from cg.utils import Process
from click.testing import CliRunner
from tests.apps.cgstats.conftest import (
    fixture_populated_stats_api,
    fixture_stats_api,
    fixture_demux_results,
    fixture_demultiplexed_flowcell,
    fixture_demultiplexed_runs,
)
from tests.apps.crunchy.conftest import fixture_sbatch_process
from tests.apps.demultiplex.conftest import (
    fixture_demultiplex_fixtures,
    fixture_flowcell_name,
    fixture_lims_novaseq_samples,
    fixture_lims_novaseq_samples_file,
    fixture_novaseq_dir,
    fixture_novaseq_run_parameters,
    fixture_raw_samples_dir,
)


@pytest.fixture(name="flowcell_full_name")
def fixture_flowcell_full_name() -> str:
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="demux_run_dir")
def fixture_demux_run_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return demultiplex_fixtures / "flowcell_runs"


@pytest.fixture(name="demux_results_dir")
def fixture_demux_results_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to a dir with demultiplexing results"""
    return demultiplex_fixtures / "demultiplexed-runs"


@pytest.fixture(name="flowcell_object")
def fixture_flowcell_object(demux_run_dir: Path, flowcell_full_name: str) -> Flowcell:
    return Flowcell(flowcell_path=demux_run_dir / flowcell_full_name)


@pytest.fixture(name="novaseq_sample_sheet_path")
def fixture_novaseq_sample_sheet_path(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "SampleSheetS2.csv"


@pytest.fixture(name="flowcell_working_directory")
def fixture_flowcell_working_directory(novaseq_dir: Path, project_dir: Path) -> Path:
    """Return the path to a working directory that will be deleted after test is run

    This is a path to a flowcell directory with the run parameters present
    """
    working_dir: Path = project_dir / novaseq_dir.name
    working_dir.mkdir(parents=True)
    existing_flowcell: Flowcell = Flowcell(flowcell_path=novaseq_dir)
    working_flowcell: Flowcell = Flowcell(flowcell_path=working_dir)
    shutil.copy(
        str(existing_flowcell.run_parameters_path), str(working_flowcell.run_parameters_path)
    )
    return working_dir


@pytest.fixture(name="demultiplex_ready_flowcell")
def fixture_demultiplex_ready_flowcell(flowcell_working_directory: Path, novaseq_dir: Path) -> Path:
    """Return the path to a working directory that is ready for demultiplexing

    This is a path to a flowcell directory with all the files necessary to start demultiplexing present
    """
    existing_flowcell: Flowcell = Flowcell(flowcell_path=novaseq_dir)
    working_flowcell: Flowcell = Flowcell(flowcell_path=flowcell_working_directory)
    shutil.copy(str(existing_flowcell.sample_sheet_path), str(working_flowcell.sample_sheet_path))
    working_flowcell.copy_complete_path.touch()
    working_flowcell.rta_complete_path.touch()
    return flowcell_working_directory


@pytest.fixture(name="sample_sheet_context")
def fixture_sample_sheet_context(cg_context: CGConfig, lims_api: LimsAPI) -> CGConfig:
    cg_context.lims_api_ = lims_api
    return cg_context


@pytest.fixture(name="demultiplex_configs")
def fixture_demultiplex_configs(project_dir: Path, demultiplex_fixtures: Path) -> dict:
    out_dir: Path = project_dir / "demultiplexed-runs"
    run_dir: Path = demultiplex_fixtures / "flowcell_runs"
    out_dir.mkdir(parents=True)
    return {
        "demultiplex": {
            "out_dir": str(out_dir),
            "run_dir": str(run_dir),
            "slurm": {"account": "test", "mail_user": "testuser@github.se"},
        }
    }


@pytest.fixture(name="demultiplexing_api")
def fixture_demultiplexing_api(
    demultiplex_configs: dict, sbatch_process: Process
) -> DemultiplexingAPI:
    demux_api = DemultiplexingAPI(config=demultiplex_configs)
    demux_api.slurm_api.process = sbatch_process
    return demux_api


@pytest.fixture(name="demultiplex_context")
def fixture_demultiplex_context(
    demultiplexing_api: DemultiplexingAPI, stats_api: StatsAPI, cg_context: CGConfig
) -> CGConfig:
    cg_context.demultiplex_api_ = demultiplexing_api
    cg_context.cg_stats_api_ = stats_api
    return cg_context


@pytest.fixture(name="cli_runner")
def fixture_cli_runner():
    """Create a CliRunner"""
    return CliRunner()
