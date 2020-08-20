"""Tests for the compress data class"""

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
