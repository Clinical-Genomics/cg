from pathlib import Path

import pytest


@pytest.fixture(name="demultiplex_fixtures")
def fixture_demultiplex_fixtures(apps_dir: Path) -> Path:
    """Return the path to the demultiplex fixtures"""
    return apps_dir / "demultiplexing"


@pytest.fixture(name="novaseq_dir")
def fixture_novaseq_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the novaseq demultiplex fixtures"""
    return demultiplex_fixtures / "novaseq_run"


@pytest.fixture(name="hiseq_dir")
def fixture_hiseq_dir(demultiplex_fixtures: Path) -> Path:
    """Return the path to the hiseq demultiplex fixtures"""
    return demultiplex_fixtures / "hiseq_run"


@pytest.fixture(name="hiseq_run_parameters")
def fixture_hiseq_run_parameters(hiseq_dir: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return hiseq_dir / "runParameters.xml"


@pytest.fixture(name="novaseq_run_parameters")
def fixture_novaseq_run_parameters(novaseq_dir: Path) -> Path:
    """Return the path to a file with hiseq run parameters"""
    return novaseq_dir / "RunParameters.xml"
