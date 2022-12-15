"""Tests for the utils module"""

from cg.utils.utils import get_string_from_list_by_pattern


def test_get_string_from_list_by_pattern():
    """Tests element extraction from a list given a string pattern."""

    # GIVEN a specific pattern and a list containing it
    pattern = "pattern"
    list_of_string = ["I do contain the pattern", "test string", "another random string"]

    # WHEN calling the filtering method
    extracted_string: str = get_string_from_list_by_pattern(list_of_string, pattern)

    # THEN the extracted string should match the one containing the pattern
    assert extracted_string == list_of_string[0]


def test_get_string_from_list_by_pattern_not_found():
    """Tests element extraction from a list given a string pattern that does not exist in the list."""

    # GIVEN a specific pattern and a list not containing it
    pattern = "I am not in the list"
    list_of_string = ["This", "is", "a", "random", "list"]

    # WHEN calling the filtering method
    extracted_string: str = get_string_from_list_by_pattern(list_of_string, pattern)

    # THEN None should be returned
    assert extracted_string is None
