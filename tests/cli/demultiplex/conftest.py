import shutil
from pathlib import Path
from typing import Dict

import pytest
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig, DemultiplexConfig
from cg.models.demultiplex.flowcell import Flowcell
from cg.utils import Process
from click.testing import CliRunner
from tests.apps.crunchy.conftest import fixture_sbatch_process
from tests.apps.demultiplex.conftest import (
    fixture_demultiplex_fixtures,
    fixture_lims_novaseq_samples,
    fixture_lims_novaseq_samples_file,
    fixture_novaseq_dir,
    fixture_novaseq_run_parameters,
    fixture_raw_samples_dir,
)


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
def fixture_demultiplex_configs(project_dir: Path) -> dict:
    out_dir: Path = project_dir / "demultiplexed-runs"
    out_dir.mkdir(parents=True)
    return {
        "demultiplex": {
            "out_dir": str(out_dir),
            "slurm": {"account": "test", "mail_user": "testuser@github.se"},
        }
    }


@pytest.fixture(name="demultiplex_context")
def fixture_demultiplex_context(
    demultiplex_configs: dict, sbatch_process: Process, cg_context: CGConfig
) -> CGConfig:
    demux_api = DemultiplexingAPI(config=demultiplex_configs)
    demux_api.slurm_api.process = sbatch_process
    cg_context.demultiplex_api_ = demux_api
    return cg_context


@pytest.fixture(name="cli_runner")
def fixture_cli_runner():
    """Create a CliRunner"""
    return CliRunner()
