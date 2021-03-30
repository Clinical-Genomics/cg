from pathlib import Path

import pytest
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


@pytest.fixture(name="cli_runner")
def fixture_cli_runner():
    """Create a CliRunner"""
    return CliRunner()
