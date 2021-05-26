from datetime import datetime

import pytest
from tests.meta.report.comparison import (
    is_float,
    is_similar_values,
    is_similar_lists,
    value_exists_in,
    dict_values_exists_in,
)


@pytest.mark.parametrize("data", [0, "0", 0.1, "0.1", "1.0", "10", True, False])
def test_is_float_with_float(data):
    # GIVEN data considered float equivalent

    # WHEN testing is_float
    is_a_float = is_float(data)

    # THEN the result should be true
    assert is_a_float


@pytest.mark.parametrize("data", [None, "a", {}, (), ""])
def test_is_float_with_non_float(data):
    # GIVEN data not considered float equivalent

    # WHEN testing is_float
    is_a_float = is_float(data)

    # THEN the result should be true
    assert not is_a_float


@pytest.mark.parametrize(
    "data",
    [
        0,
        "0",
        0.1,
        "0.1",
        "1.0",
        "10",
        True,
        False,
        None,
        "",
        (),
        [],
        {},
        ["a", "b", "c"],
        {"numbers": 123},
        {"dict": {"text": "text"}},
        datetime.now(),
    ],
)
def test_is_similar_values_data_compared_to_equal(data):
    # GIVEN data

    # WHEN using two equal data items
    is_similar = is_similar_values(data, data)

    # THEN the result should be similar
    assert is_similar


@pytest.mark.parametrize(
    "data_pair",
    [(0, "0"), (0.1, "0.1"), (1.33, "1.3"), (datetime.now(), str(datetime.now().date()))],
)
def test_is_similar_values_data_compared_to_similar(data_pair):
    # GIVEN data and similar data
    data, similar_data = data_pair

    # WHEN using data and similar data
    is_similar = is_similar_values(data, similar_data)

    # THEN the result should be similar
    assert is_similar


@pytest.mark.parametrize(
    "data_pair",
    [(0, "1"), (0.1, None), (None, "1.3"), (str(datetime.now().date()), datetime.now())],
)
def test_is_similar_values_data_compared_to_non_similar(data_pair):
    # GIVEN data and similar data
    data, non_similar_data = data_pair

    # WHEN using data and non similar data
    is_similar = is_similar_values(data, non_similar_data)

    # THEN the result should not be similar
    assert not is_similar


@pytest.mark.parametrize(
    "data",
    [None, "abc", [1, 2, 3], ["a", "b", "c"], ["a", 1, "1", None, [], {}, (), {}, datetime.now()]],
)
def test_is_similar_lists_compared_to_equal(data):
    # GIVEN data

    # WHEN using two equal data items
    is_similar = is_similar_lists(data, data)

    # THEN the result should be similar
    assert is_similar


@pytest.mark.parametrize("data", ["some_text", 1.3, 123, datetime.now(), True])
def test_value_exists_in_text(data):
    # GIVEN data and a text containing that data
    data_in_text = "this is a text " + str(data) + " and then some more text"

    # WHEN running function
    exists = value_exists_in(data, data_in_text)

    # THEN the result should be True
    assert exists


@pytest.mark.parametrize("data", ["some_text", 1.3, 123, datetime.now()])
def test_value_exists_not_in_text(data):
    # GIVEN data and a text not missing that data
    data_not_in_text = "this is a text and then some more text"

    # WHEN running function
    exists = value_exists_in(data, data_not_in_text)

    # THEN the result should be True
    assert not exists


@pytest.mark.parametrize(
    "data_pair",
    [
        (
            {"text": "some_text", "dict": {"number": 1.3, "list": ["abc", 123, True]}},
            "Report containing some_text the number 1.3, the list abc and 123",
        )
    ],
)
def test_dict_values_exists_in_text(data_pair):
    # GIVEN data and a text containing that data
    data, data_in_text = data_pair

    # WHEN running function
    exists = dict_values_exists_in(data, data_in_text)

    # THEN the result should be True
    assert exists


@pytest.mark.parametrize(
    "data_pair",
    [
        (
            {
                "text": "some_text",
                "dict": {"number": 1.3, "list": ["abc", 123, datetime.now(), True]},
            },
            "Report not containing data",
        )
    ],
)
def test_dict_values_not_existing_in_text(data_pair):
    # GIVEN data and a text not containing that data
    data, data_in_text = data_pair

    # WHEN running function
    exists = dict_values_exists_in(data, data_in_text)

    # THEN the result should be False
    assert not exists
