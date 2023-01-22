from pathlib import Path

import pytest

from tests.apps.demultiplex.conftest import fixture_novaseq_dir
from tests.cli.demultiplex.conftest import fixture_demultiplexed_flow_cells_working_directory
from tests.models.demultiplexing.conftest import (
    fixture_flowcell_path,
    fixture_flow_cell_runs,
)


@pytest.fixture(name="correct_flow_cell")
def fixture_correct_flow_cell() -> str:
    """Correct flow cell name"""
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="incorrect_flow_cell_too_long")
def fixture_incorrect_flow_cell_too_long() -> str:
    """Incorrect flow cell name"""
    return "201203_A00689_0200_AHVKJCDRXX_r"


@pytest.fixture(name="incorrect_flow_cell_extension")
def fixture_incorrect_flow_cell_extension() -> str:
    """Incorrect flow cell name"""
    return "201203_A00689_0200_AHVKJCDRXX.someextension"


@pytest.fixture(name="incorrect_flow_cell_name")
def fixture_incorrect_flow_cell_name() -> str:
    """Incorrect flow cell name"""
    return "201203_A00689_0200_AZZZZZZZZZ"


@pytest.fixture(name="correct_flow_cell_path")
def fixture_correct_flow_cell_path(
    demultiplexed_flow_cells_working_directory, correct_flow_cell
) -> Path:
    """Full path to a correctly named flow cell directory in demultiplexed-runs"""
    return Path(demultiplexed_flow_cells_working_directory, correct_flow_cell)


@pytest.fixture(name="incorrect_flow_cell_path_too_long")
def fixture_incorrect_flow_cell_path_too_long(
    demultiplexed_flow_cells_working_directory, incorrect_flow_cell_too_long
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs"""
    return Path(demultiplexed_flow_cells_working_directory, incorrect_flow_cell_too_long)


@pytest.fixture(name="incorrect_flow_cell_path_extension")
def fixture_incorrect_flow_cell_path_extension(
    demultiplexed_flow_cells_working_directory, incorrect_flow_cell_extension
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs"""
    return Path(demultiplexed_flow_cells_working_directory, incorrect_flow_cell_extension)


@pytest.fixture(name="nonexistent_flow_cell_path")
def fixture_nonexistent_flow_cell_path(
    demultiplexed_flow_cells_working_directory, incorrect_flow_cell_name
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs"""
    return Path(demultiplexed_flow_cells_working_directory, incorrect_flow_cell_name)
