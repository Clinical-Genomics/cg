import shutil
from pathlib import Path

import pytest
from cg.apps.demultiplex.flowcell import Flowcell
from cg.apps.lims import LimsAPI
from click.testing import CliRunner
from tests.apps.demultiplex.conftest import (
    fixture_demultiplex_fixtures,
    fixture_novaseq_dir,
    fixture_novaseq_run_parameters,
)


@pytest.fixture(name="novaseq_sample_sheet_path")
def fixture_novaseq_sample_sheet_path(demultiplex_fixtures: Path) -> Path:
    return demultiplex_fixtures / "SampleSheetS2.csv"


@pytest.fixture(name="sample_sheet_context")
def fixture_sample_sheet_context(lims_api: LimsAPI) -> dict:
    return {"lims_api": lims_api}


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


@pytest.fixture(name="cli_runner")
def fixture_cli_runner():
    """Create a CliRunner"""
    return CliRunner()
