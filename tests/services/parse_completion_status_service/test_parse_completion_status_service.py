"""Module to test the parse_completion_status_service"""

from datetime import datetime
from pathlib import Path

from cg.services.parse_run_completion_status_service.parse_run_completion_status_service import (
    ParseRunCompletionStatusService,
)


def test_get_start_time(run_completion_status_path: Path, expected_start_time: datetime):
    """Test to get the start time."""
    # GIVEN a parse run completion status service and a path to the run completion status file
    parser = ParseRunCompletionStatusService()

    # WHEN getting the start time
    start_time: datetime = parser.get_start_time(
        run_completion_status_path=run_completion_status_path
    )

    # THEN assert the start time is correct
    assert start_time == expected_start_time


def test_get_end_time(run_completion_status_path: Path, expected_end_time: datetime):
    """Test to get the end time."""
    # GIVEN a parse run completion status service and a path to the run completion status file
    parser = ParseRunCompletionStatusService()

    # WHEN getting the end time
    end_time: datetime = parser.get_end_time(run_completion_status_path=run_completion_status_path)

    # THEN assert the end time is correct
    assert end_time == expected_end_time
