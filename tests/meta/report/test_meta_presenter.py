"""Tests the Presenter class"""
from cg.meta.report.presenter import Presenter


def test_present_float_string():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter.process_float_string(None, 0)

    # THEN we should get 'N/A' back
    assert presentable_string == 'N/A'


def test_present_date():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter.process_datetime(None)

    # THEN we should get 'N/A' back
    assert presentable_string == 'N/A'


def test_present_string():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter.process_string(None)

    # THEN we should get 'N/A' back
    assert presentable_string == 'N/A'


def test_present_int():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter.process_int(None)

    # THEN we should get 'N/A' back
    assert presentable_string == 'N/A'


def test_present_set():
    # GIVEN

    # WHEN formatting None
    presentable_string = Presenter.process_set(None)

    # THEN we should get 'N/A' back
    assert presentable_string == 'N/A'
