"""Tests for the utils module"""

import pytest

from cg.cli.utils import is_case_name_allowed
from cg.utils.utils import get_hamming_distance


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
