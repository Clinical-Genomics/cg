"""Tests the Presenter class"""
from cg.meta.report.presenter import Presenter


def test_present_float_string():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter().process_float_string(None, 0)

    # THEN we should get 'N/A' back
    assert presentable_string == Presenter().DEFAULT_NA


def test_present_date():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter().process_datetime(None)

    # THEN we should get 'N/A' back
    assert presentable_string == Presenter().DEFAULT_NA


def test_present_string():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter().process_string(None)

    # THEN we should get 'N/A' back
    assert presentable_string == Presenter().DEFAULT_NA


def test_present_int():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter().process_int(None)

    # THEN we should get 'N/A' back
    assert presentable_string == Presenter().DEFAULT_NA


def test_present_set():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter().process_set(None)

    # THEN we should get 'N/A' back
    assert presentable_string == Presenter().DEFAULT_NA


def test_present_dict():
    # GIVEN a dict to present
    dict_to_present = {
        "nested_dict": {"string_key": "string_value", "none_key": None, "empty_key": ""}
    }

    # WHEN formatting dict
    presentable_dict = Presenter().process_dict(dict_to_present)

    # THEN we should get 'N/A' back
    assert presentable_dict["nested_dict"]["string_key"] == "string_value"
    assert presentable_dict["nested_dict"]["none_key"] == Presenter().DEFAULT_NA
    assert presentable_dict["nested_dict"]["empty_key"] == Presenter().DEFAULT_NA
