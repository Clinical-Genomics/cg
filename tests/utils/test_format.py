"""Tests for the formatting module."""

from cg.utils.dict import get_list_from_dictionary


def test_get_list_from_dictionary():
    """Test the formatting of the flattened dictionary."""

    # GIVEN a mock dictionary
    mock_dict = {"a": 1, "b": 2, "c": None, "d": "3"}

    # GIVEN the expected output
    expected_output = ["a", 1, "b", 2, "d", "3"]

    # WHEN calling the function
    flattened_dict = get_list_from_dictionary(mock_dict)

    # THEN assert the output should match the expected list
    assert flattened_dict == expected_output


def test_get_list_from_dictionary_empty_input():
    """Test the formatting of the flattened dictionary."""

    # GIVEN an empty dictionary
    mock_dict = {}

    # WHEN calling the function
    flattened_dict = get_list_from_dictionary(mock_dict)

    # THEN assert the output matches the expected list
    assert not flattened_dict
