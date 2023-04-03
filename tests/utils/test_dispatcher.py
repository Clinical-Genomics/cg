from typing import List, Tuple, Callable, Any
import pytest
from cg.utils.dispatcher import Dispatcher


def test_dispatch_table_generation(
    param1: str = None, param2: str = None, param3: str = None, param4: str = None
):
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
        {"param1": param1, "param2": param2, "param3": param3, "param4": param4},
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


def test_call_matching_function(a: int = 1, b: int = 2, c: int = 3, x: int = 5, y: int = 4):
    def foo(a, b, c):
        return a + b + c

    def bar(x, y):
        return x * y

    dispatcher = Dispatcher([foo, bar], input_dict={"a": a, "b": b, "c": c, "x": x, "y": y})
    assert dispatcher({"a": a, "b": b, "c": c}) == 6
    assert dispatcher({"x": x, "y": y}) == 20


def test_call_non_matching_function(a: int = 1, b: int = 2, c: int = 3, x: int = 5, y: int = 4):
    def foo(a, b, c):
        return a + b + c

    def bar(x, y):
        return x * y

    dispatcher = Dispatcher([foo, bar], input_dict={"a": a, "b": b, "c": c, "x": x, "y": y})
    with pytest.raises(ValueError):
        dispatcher({"a": a, "b": b})


def test_call_for_function_without_parameters():
    def foo():
        return 1

    dispatcher = Dispatcher([foo], input_dict={})
    assert dispatcher({}) == 1


def test_call_for_function_with_same_number_of_parameters():
    def foo(a, b):
        return a + b

    def bar(c, d):
        return c * d

    dispatcher = Dispatcher([foo, bar], input_dict={"a": 1, "b": 2, "c": 3, "d": 4})
    assert dispatcher({"a": 1, "b": 2}) == 3
    assert dispatcher({"c": 3, "d": 4}) == 12


def test_call_dictionary_extra_parameters_not_in_functions():
    def foo(a, b):
        return a + b

    def bar(c, d):
        return c * d

    dispatcher = Dispatcher([foo, bar], input_dict={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})
    assert dispatcher({"a": 1, "b": 2}) == 3
