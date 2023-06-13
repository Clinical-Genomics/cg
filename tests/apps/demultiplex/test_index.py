"""Tests for functions related to indexes."""
from typing import List

from cg.apps.demultiplex.sample_sheet.index import Index, get_valid_indexes


def test_get_valid_indexes():
    """Test that the function get_valid_indexes returns a list of Index objects."""
    # GIVEN a sample sheet api

    # WHEN fetching the indexes
    indexes: List[Index] = get_valid_indexes()

    # THEN assert that the indexes are correct
    assert len(indexes) > 0
    assert isinstance(indexes[0], Index)
