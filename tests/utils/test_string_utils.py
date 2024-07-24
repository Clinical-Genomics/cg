"""Test for the string utilities,"""

from cg.utils.string import get_element_from_split


def test_get_element_from_split():

    # GIVEN a string with a seperator
    separated_string: str = "one_two_three_four"

    # WHEN getting an element divided by a separator based on the position
    element: str = get_element_from_split(value=separated_string, element_position=2, split="_")

    # THEN the expected element is retured
    assert element == "two"
