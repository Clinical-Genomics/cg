"""Tests for the compress data class"""

from datetime import datetime
from pathlib import Path

from cg.models import CompressionData


def test_get_run_name():
    """Test that the correct run name is returned"""
    # GIVEN a file path that ends with a run name
    file_path = Path("/path/to/dir")
    run_name = "a_run"
    # GIVEN a compression data object
    compression_obj = CompressionData(file_path / run_name)

    # WHEN fetching the run name
    # THEN assert the correct run name is returned
    assert compression_obj.run_name == run_name


def test_get_change_date(compression_object):
    """Test to get the date time for when a file was changed"""
    # GIVEN a existing file
    file_path = compression_object.spring_path
    file_path.touch()

    # WHEN fetching the date when file was created
    change_date = compression_object.get_change_date(file_path)

    # THEN check that it is the same date as today
    assert change_date.date() == datetime.today().date()
