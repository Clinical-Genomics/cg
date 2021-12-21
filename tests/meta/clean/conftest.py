from pathlib import Path

import pytest
from tests.cli.demultiplex.conftest import fixture_demultiplexed_flowcells_working_directory


@pytest.fixture(name="correct_flowcell")
def fixture_correct_flowcell() -> str:
    """Correct flowcell name"""
    return "201203_A00689_0200_AHVKJCDRXX"


@pytest.fixture(name="incorrect_flowcell_too_long")
def fixture_incorrect_flowcell_too_long() -> str:
    """Incorrect flowcell name"""
    return "201203_A00689_0200_AHVKJCDRXX_r"


@pytest.fixture(name="incorrect_flowcell_extension")
def fixture_incorrect_flowcell_extension() -> str:
    """Incorrect flowcell name"""
    return "201203_A00689_0200_AHVKJCDRXX.someextension"


@pytest.fixture(name="nonexistent_flowcell")
def fixture_nonexistent_flowcell() -> str:
    """Incorrect flowcell name"""
    return "201203_A00689_0200_AZZZZZZZZZ"


@pytest.fixture(name="correct_flowcell_path")
def fixture_correct_flowcell_path(
    demultiplexed_flowcells_working_directory, correct_flowcell
) -> Path:
    """Full path to a correctly named flowcell directory in demultiplexed-runs"""
    return Path(demultiplexed_flowcells_working_directory, correct_flowcell)


@pytest.fixture(name="incorrect_flowcell_path_too_long")
def fixture_incorrect_flowcell_path_too_long(
    demultiplexed_flowcells_working_directory, incorrect_flowcell_too_long
) -> Path:
    """Full path to an incorrectly named flowcell directory in demultiplexed-runs"""
    return Path(demultiplexed_flowcells_working_directory / incorrect_flowcell_too_long)


@pytest.fixture(name="incorrect_flowcell_path_extension")
def fixture_incorrect_flowcell_path_extension(
    demultiplexed_flowcells_working_directory, incorrect_flowcell_extension
) -> Path:
    """Full path to an incorrectly named flowcell directory in demultiplexed-runs"""
    return Path(demultiplexed_flowcells_working_directory / incorrect_flowcell_extension)


@pytest.fixture(name="nonexistent_flowcell_path")
def fixture_nonexistent_flowcell_path(
    demultiplexed_flowcells_working_directory, nonexistent_flowcell
) -> Path:
    """Full path to an incorrectly named flowcell directory in demultiplexed-runs"""
    return Path(demultiplexed_flowcells_working_directory / nonexistent_flowcell)
