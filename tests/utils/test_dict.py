"""Tests for the dict module."""
from pathlib import Path


from cg.utils.dict import get_list_from_dictionary, get_full_path_dictionary


def test_get_list_from_dictionary():
    """Test the formatting of the flattened dictionary."""

    # GIVEN a mock dictionary
    mock_dict = {"a": 1, "b": 2, "c": None, "d": "3"}

    # GIVEN the expected output
    expected_output = ["a", 1, "b", 2, "d", "3"]

    # WHEN calling the function
    flattened_dict: dict = get_list_from_dictionary(mock_dict)

    # THEN assert the output should match the expected list
    assert flattened_dict == expected_output


def test_get_list_from_dictionary_empty_input():
    """Test the formatting of the flattened dictionary."""

    # GIVEN an empty dictionary
    mock_dict = {}

    # WHEN calling the function
    flattened_dict: dict = get_list_from_dictionary(mock_dict)

    # THEN assert the output matches the expected list
    assert not flattened_dict


def test_get_full_path_dictionary(hk_file) -> dict:
    """Test full path parsing of a dictionary."""

    # GIVEN a housekeeper file, an empty value, and a dictionary containing it
    file_dict: dict = {"file": hk_file, "empty": None}

    # WHEN obtaining the full path of the elements of a dictionary
    file_full_path_dictionary: dict = get_full_path_dictionary(file_dict)

    # THEN the obtained dictionary path should be absolute
    assert Path(file_full_path_dictionary["file"]).is_absolute()
    assert file_full_path_dictionary["empty"] is None
