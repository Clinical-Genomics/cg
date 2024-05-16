"""Tests for the utils module"""

import pytest

from cg.cli.utils import is_case_name_allowed
from cg.utils.utils import get_hamming_distance, get_string_from_list_by_pattern


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


def test_get_hamming_distance():
    """Test that getting the hamming distance between two strings works as expected."""
    # GIVEN two different strings with the same length
    str_1: str = "1234567"
    str_2: str = "7654321"

    # WHEN getting the hamming distance between both strings

    # THEN is equal to the number of different characters between the strings
    assert get_hamming_distance(str_1=str_1, str_2=str_2) == 6

    # WHEN getting the hamming distance between one string and itself

    # THEN is equal to zero
    assert get_hamming_distance(str_1=str_1, str_2=str_1) == 0


def test_get_hamming_distance_different_lengths():
    """Test that getting the hamming distance between two strings works as expected."""
    # GIVEN two strings with different lengths
    str_1: str = "12345678"
    str_2: str = "123456789"

    # WHEN getting the hamming distance between both strings
    with pytest.raises(KeyError) as exc_info:
        # THEN an error is raised
        get_hamming_distance(str_1=str_1, str_2=str_2)
        assert (
            str(exc_info.value)
            == "The two strings must have the same length to calculate distance!"
        )


@pytest.mark.parametrize(
    "case_name, expected_behaviour",
    [
        ("valid-case-name123", True),
        ("invalid_case_name", False),
        ("invalid-special-character()", False),
    ],
)
def test_is_case_name_valid(case_name: str, expected_behaviour: bool):
    assert is_case_name_allowed(case_name) == expected_behaviour
