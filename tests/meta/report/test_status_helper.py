""" Test the status database report helper"""
from datetime import datetime, timedelta

from cg.meta.report.status_helper import StatusHelper
from cg.tests.store_helpers import add_analysis


def test_get_previous_report_version_when_only_one(store):

    # GIVEN two analyses for the given family
    first_analysis = add_analysis(store)

    # WHEN fetching previous_report_version
    report_version = StatusHelper.get_previous_report_version(first_analysis)

    # THEN the version should be None
    assert not report_version


def test_get_previous_report_version_when_two(store):

    # GIVEN two analyses for the given family
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = add_analysis(store, completed_at=datetime.now())
    add_analysis(store, first_analysis.family, completed_at=yesterday)

    # WHEN fetching previous_report_version
    report_version = StatusHelper.get_previous_report_version(first_analysis)

    # THEN the version should be 1
    assert report_version == 1


def test_first_analysis_when_only_one(store):

    # GIVEN one analysis for the given family
    analysis = add_analysis(store)
    assert len(analysis.family.analyses) == 1

    # WHEN fetching report_version
    report_version = StatusHelper.get_report_version(analysis)

    # THEN the version should be 1
    assert report_version == 1


def test_first_analysis_when_two(store):

    # GIVEN two analyses for the given family
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = add_analysis(store, completed_at=datetime.now())
    second_analysis = add_analysis(store, first_analysis.family, completed_at=yesterday)

    # WHEN fetching report_version
    report_version = StatusHelper.get_report_version(second_analysis)

    # THEN the version should be 1
    assert report_version == 1


def test_second_analysis_when_two(store):

    # GIVEN two analyses for the given family
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = add_analysis(store, completed_at=datetime.now())
    second_analysis = add_analysis(store, first_analysis.family, completed_at=yesterday)
    assert first_analysis.family.analyses.index(second_analysis) == 1
    assert first_analysis.family.analyses.index(first_analysis) == 0

    # WHEN fetching report_version
    report_version = StatusHelper.get_report_version(second_analysis)

    # THEN the version should be 1
    assert report_version == 1


