import pytest

from cg.apps.orderform.orderform_parser import OrderformParser
from cg.exc import OrderFormError


class Shape:
    def __init__(self, name, sides):
        self.name = name
        self.sides = sides


def test__get_single_value_when_same():
    """Test method to get a single value"""

    # GIVEN a bunch of items with an attribute where all items have the same value
    expected_sides: int = 4
    items: [{}] = [
        Shape(name="rhombus", sides=expected_sides),
        Shape(name="square", sides=expected_sides),
    ]

    # WHEN getting a single value
    single_value: int = OrderformParser._get_single_value(
        items_id="items", items=items, attr="sides"
    )

    # THEN assert that the returned value was the expected one
    assert single_value == expected_sides


def test__get_single_value_when_different():
    """Test method to get a single value"""

    # GIVEN a bunch of items with an attribute where all items have different values
    items: [{}] = [Shape(name="ball", sides=1), Shape(name="square", sides=4)]

    # WHEN getting a single value but items contains different values
    # THEN assert that the expected exception is raised
    with pytest.raises(OrderFormError):
        OrderformParser._get_single_value(items_id="items", items=items, attr="sides")


def test__get_single_value_when_same():
    """Test method to get a single value"""

    # GIVEN a bunch of items with an attribute where all items have the same value
    expected_sides: [] = ["A", "B", "C", "D"]
    items: [{}] = [
        Shape(name="rhombus", sides=expected_sides),
        Shape(name="square", sides=expected_sides),
    ]

    # WHEN getting a single value
    single_value: [] = OrderformParser._get_single_set(items_id="items", items=items, attr="sides")

    # THEN assert that the returned value was the expected one
    assert single_value == set(expected_sides)


def test__get_single_set_when_different():
    """Test method to get a single value"""

    # GIVEN a bunch of items with an attribute where all items have different values
    items: [{}] = [
        Shape(name="ball", sides=["outside", "inside"]),
        Shape(name="square", sides=["r", "l", "u", "d"]),
    ]

    # WHEN getting a single value but items contains different values
    # THEN assert that the expected exception is raised
    with pytest.raises(OrderFormError):
        OrderformParser._get_single_set(items_id="items", items=items, attr="sides")
