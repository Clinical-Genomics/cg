from typing import List
import pytest
from cg.utils.dispatcher import Dispatcher
from tests.store_helpers import StoreHelpers
from cg.store import Store
from cg.store.models import Sample
from cg.constants.invoice import CustomerNames


def test_dispatch_table_generation(
    param1: str = None, param2: str = None, param3: str = None, param4: str = None
):
    """Test that the dispatch table is generated correctly."""

    # Given a list of functions with different parameters
    def test_function_one(param1: str):
        pass

    def test_function_two(param1: str, param2: str):
        pass

    def test_function_three(param1: str, param2: str, param3: str):
        pass

    def test_function_four(param4: str):
        pass

    # When generating the dispatch table
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
    # Then the dispatch table should contain the correct keys and values
    assert dispatcher.dispatch_table.keys() == expected_table.keys()
    for key in expected_table:
        assert dispatcher.dispatch_table[key] == expected_table[key]


def test_call_matching_function(a: int = 1, b: int = 2, c: int = 3, x: int = 5, y: int = 4):
    """Test that the dispatcher can be called with a dictionary that matches one of the functions."""

    # Given two functions
    def foo(a, b, c):
        return a + b + c

    def bar(x, y):
        return x * y

    # When calling the dispatcher with a dictionary that matches one of the functions
    dispatcher = Dispatcher([foo, bar], input_dict={"a": a, "b": b, "c": c, "x": x, "y": y})

    # Then the dispatcher should return the correct result
    assert dispatcher({"a": a, "b": b, "c": c}) == 6
    assert dispatcher({"x": x, "y": y}) == 20


def test_call_non_matching_function(a: int = 1, b: int = 2, c: int = 3, x: int = 5, y: int = 4):
    """Test that the dispatcher raises an error when called with a dictionary that does not match any of the functions."""

    # Given two functions
    def foo(a, b, c):
        return a + b + c

    def bar(x, y):
        return x * y

    # When calling the dispatcher with a dictionary that does not match any of the functions
    dispatcher = Dispatcher([foo, bar], input_dict={"a": a, "b": b, "c": c, "x": x, "y": y})

    # Then the dispatcher should raise an error
    with pytest.raises(ValueError):
        dispatcher({"a": a, "b": b})


def test_call_for_function_without_parameters():
    """Test that the dispatcher can be called with a function that has no parameters."""

    # GIVEN a function with no parameters
    def foo():
        return 1

    # WHEN calling the dispatcher with a dictionary that has no parameters
    dispatcher = Dispatcher([foo], input_dict={})

    # THEN the dispatcher should return the correct result
    assert dispatcher({}) == 1


def test_call_for_function_with_same_number_of_parameters():
    """Test that the dispatcher can be called with a dictionary that has the same number of parameters as the functions."""

    # GIVEN two functions with the same number of parameters
    def foo(a, b):
        return a + b

    def bar(c, d):
        return c * d

    # WHEN calling the dispatcher with a dictionary that has the same number of parameters as the functions
    dispatcher = Dispatcher([foo, bar], input_dict={"a": 1, "b": 2, "c": 3, "d": 4})

    # THEN the dispatcher should return the correct result for each function
    assert dispatcher({"a": 1, "b": 2}) == 3
    assert dispatcher({"c": 3, "d": 4}) == 12


def test_call_dictionary_extra_parameters_not_in_functions():
    """Test that the dispatcher can be called with a dictionary that has extra parameters that are not in the functions."""

    # GIVEN two functions with different parameters
    def foo(a, b):
        return a + b

    def bar(c, d):
        return c * d

    # WHEN calling the dispatcher with a dictionary that has extra parameters
    dispatcher = Dispatcher([foo, bar], input_dict={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})

    # THEN the dispatcher should return the correct result
    assert dispatcher({"a": 1, "b": 2}) == 3


def test_call_with_status_db_functions(
    store: Store,
    helpers: StoreHelpers,
    customer_internal_id: str = CustomerNames.cust001,
    test_subject: str = "test_subject",
    is_tumour: bool = True,
):
    """Test that the dispatcher can be used to call functions in the status db"""

    # GIVEN a database with a customer, a subject and two samples
    helpers.add_sample(store, subject_id=test_subject)
    helpers.add_sample(store, subject_id=test_subject, is_tumour=False)

    # WHEN calling the dispatcher with the customer and subject id
    dispatcher = Dispatcher(
        functions=[
            store.get_samples_by_customer_and_subject_id,
            store.get_samples_by_customer_subject_id_and_is_tumour,
        ],
        input_dict={
            "customer_internal_id": customer_internal_id,
            "subject_id": test_subject,
            "is_tumour": is_tumour,
        },
    )
    # THEN the dispatcher should return the correct samples
    samples: List[Sample] = dispatcher(
        {"customer_internal_id": customer_internal_id, "subject_id": test_subject}
    )
    for sample in samples:
        assert sample.customer.internal_id == customer_internal_id
        assert sample.subject_id == test_subject
