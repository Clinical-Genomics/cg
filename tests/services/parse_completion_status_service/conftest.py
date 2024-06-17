"""conftest for parse_completion_status_service tests."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.utils.time import DATE_TIME_FORMAT


@pytest.fixture()
def run_completion_status_path(novaseq_x_flow_cell_dir) -> Path:
    """Return the path to the run completion status file."""
    return Path(
        novaseq_x_flow_cell_dir,
        "RunCompletionStatus.xml",
    )


@pytest.fixture()
def expected_start_time() -> datetime:
    """Return the expected start time."""
    return datetime.strptime("2023-11-08T16:06:11", DATE_TIME_FORMAT)


@pytest.fixture()
def expected_end_time() -> datetime:
    """Return the expected end time."""
    return datetime.strptime("2023-11-09T15:24:13", DATE_TIME_FORMAT)
