from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def correct_flow_cell_name(bcl2fastq_flow_cell_full_name: str) -> str:
    """Correct flow cell name."""
    return bcl2fastq_flow_cell_full_name


@pytest.fixture(scope="function")
def incorrect_flow_cell_too_long(correct_flow_cell_name: str) -> str:
    """Incorrect flow cell name."""
    return correct_flow_cell_name + "_r"


@pytest.fixture(scope="function")
def incorrect_flow_cell_extension(correct_flow_cell_name: str) -> str:
    """Incorrect flow cell name."""
    return correct_flow_cell_name + ".someextension"


@pytest.fixture(scope="function")
def incorrect_flow_cell_name() -> str:
    """Incorrect flow cell name."""
    return "201203_A00689_0200_AZZZZZZZZZ"


@pytest.fixture(scope="function")
def correct_flow_cell_path(
    tmp_demultiplexed_runs_directory: Path, correct_flow_cell_name: str
) -> Path:
    """Full path to a correctly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, correct_flow_cell_name)


@pytest.fixture(scope="function")
def incorrect_flow_cell_path_too_long(
    tmp_demultiplexed_runs_directory: Path, incorrect_flow_cell_too_long: str
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, incorrect_flow_cell_too_long)


@pytest.fixture(scope="function")
def incorrect_flow_cell_path_extension(
    tmp_demultiplexed_runs_directory: Path, incorrect_flow_cell_extension: str
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, incorrect_flow_cell_extension)


@pytest.fixture(name="non-existent_flow_cell_path", scope="function")
def non_existent_flow_cell_path(
    tmp_demultiplexed_runs_directory: Path, incorrect_flow_cell_name: str
) -> Path:
    """Full path to an incorrectly named flow cell directory in demultiplexed-runs."""
    return Path(tmp_demultiplexed_runs_directory, incorrect_flow_cell_name)
