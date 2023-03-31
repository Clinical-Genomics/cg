from typing import List, Tuple, Callable, Any
import pytest
from cg.utils.dispatcher import Dispatcher


def test_dispatch_table_generation():
    def test_function_one(param1: str):
        pass

    def test_function_two(param1: str, param2: str):
        pass

    def test_function_three(param1: str, param2: str, param3: str):
        pass

    def test_function_four(param4: str):
        pass

    dispatcher = Dispatcher(
        [test_function_one, test_function_two, test_function_three, test_function_four],
        ("param1",),
        (
            "param1",
            "param2",
        ),
        (
            "param1",
            "param2",
            "param3",
        ),
        ("param4",),
    )

    expected_table = {
        ("param1",): test_function_one,
        ("param1", "param2"): test_function_two,
        ("param1", "param2", "param3"): test_function_three,
        ("param4",): test_function_four,
    }
    assert dispatcher.dispatch_table.keys() == expected_table.keys()
    for key in expected_table:
        assert dispatcher.dispatch_table[key] == expected_table[key]


def test_call_matching_function(a=1, b=2, c=3, x=5, y=4):
    def foo(a, b, c):
        test = a + b + c
        return a + b + c

    def bar(x, y):
        return x * y

    dispatcher = Dispatcher([foo, bar], input_dict={"a": a, "b": b, "c": c, "x": x, "y": y})
    assert dispatcher({"a": a, "b": b, "c": c}) == 6
    assert dispatcher({"x": x, "y": y}) == 20
