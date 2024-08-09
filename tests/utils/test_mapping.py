"""Tests for the mapping utils module."""

import pytest

from cg.exc import CgError
from cg.utils.mapping import get_item_by_pattern_in_source


def test_get_item_by_pattern():
    # GIVEN a mapping dictionary

    mapping_dict: dict[str, any] = {"key_one": "one", "key_two": "two", "key_three": "three"}

    # WHEN retrieving an item by a pattern
    item: any = get_item_by_pattern_in_source(source="key_three_dee", pattern_map=mapping_dict)

    # THEN the correct items is returned
    assert item == "three"


def test_get_item_by_pattern_raises_error():
    # GIVEN a mapping dictionary

    mapping_dict: dict[str, any] = {"key_one": "one", "key_two": "two", "key_three": "three"}

    # WHEN retrieving an item by a pattern
    with pytest.raises(CgError):
        get_item_by_pattern_in_source(source="key_not_there", pattern_map=mapping_dict)

    # THEN an error is raised
