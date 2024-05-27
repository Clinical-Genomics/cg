"""conftest for parse_completion_status_service tests."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.services.parse_run_completion_status_service.parse_run_completion_status_service import (
    DATE_TIME_FORMAT,
)


@pytest.fixture()
def run_completion_status_path() -> Path:
    """Return the path to the run completion status file."""
    return Path(
        "tests",
        "fixtures",
        "apps",
        "demultiplexing",
        "flow_cells",
        "20231108_LH00188_0028_B22F52TLT3",
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
