"""Test for the string utilities."""

import pytest

from cg.exc import CgError
from cg.utils.string import get_element_from_split


def test_get_element_from_split():

    # GIVEN a string with a seperator
    separated_string: str = "zero_one_two_three"

    # WHEN getting an element divided by a separator based on the position
    element: str = get_element_from_split(value=separated_string, element_position=2, split="_")

    # THEN the expected element is returned
    assert element == "two"


def test_get_element_from_split_error():

    # GIVEN a string with a seperator
    separated_string: str = "zero_one_two_three"

    # WHEN getting an element divided by a separator based on the position that is out of bounds
    with pytest.raises(CgError):
        get_element_from_split(value=separated_string, element_position=12, split="_")

        # THEN an error is raised
