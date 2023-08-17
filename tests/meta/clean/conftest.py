from pathlib import Path

import pytest


@pytest.fixture(name="correct_flow_cell_name")
def fixture_correct_flow_cell_name(bcl2fastq_flow_cell_full_name: str) -> str:
    """Correct flow cell name."""
    return bcl2fastq_flow_cell_full_name


@pytest.fixture(name="incorrect_flow_cell_too_long")
def fixture_incorrect_flow_cell_too_long(correct_flow_cell_name: str) -> str:
    """Incorrect flow cell name."""
    return correct_flow_cell_name + "_r"


@pytest.fixture(name="incorrect_flow_cell_extension")
def fixture_incorrect_flow_cell_extension(correct_flow_cell_name: str) -> str:
    """Incorrect flow cell name."""
    return correct_flow_cell_name + ".someextension"


@pytest.fixture(name="incorrect_flow_cell_name")
def fixture_incorrect_flow_cell_name() -> str:
    """Incorrect flow cell name."""
    return "201203_A00689_0200_AZZZZZZZZZ"


@pytest.fixture(name="correct_flow_cell_path")
def fixture_correct_flow_cell_path(
    tmp_demultiplexed_runs_directory, correct_flow_cell_name
) -> Path:
    """Full path to a correctly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, correct_flow_cell_name)


@pytest.fixture(name="incorrect_flow_cell_path_too_long")
def fixture_incorrect_flow_cell_path_too_long(
    tmp_demultiplexed_runs_directory, incorrect_flow_cell_too_long
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, incorrect_flow_cell_too_long)


@pytest.fixture(name="incorrect_flow_cell_path_extension")
def fixture_incorrect_flow_cell_path_extension(
    tmp_demultiplexed_runs_directory, incorrect_flow_cell_extension
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, incorrect_flow_cell_extension)


@pytest.fixture(name="non-existent_flow_cell_path")
def fixture_non_existent_flow_cell_path(
    tmp_demultiplexed_runs_directory, incorrect_flow_cell_name
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, incorrect_flow_cell_name)
