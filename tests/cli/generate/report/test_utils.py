"""Tests utils for generating delivery reports"""
from datetime import datetime

import click.exceptions
import pytest
from cgmodels.cg.constants import Pipeline

from cg.cli.generate.report.utils import (
    resolve_report_case,
    resolve_report_api,
    resolve_report_api_pipeline,
    resolve_report_analysis_started,
)
from cg.meta.report.balsamic_umi import BalsamicUmiReportAPI
from tests.mocks.report import MockMipDNAReportAPI


def test_resolve_report_case(click_context, case_id):
    """Tests case object extraction for delivery report given a valid case_id"""

    # GIVEN a delivery report click context

    # WHEN resolving a report case ID
    case_obj = resolve_report_case(click_context, case_id)

    # THEN a valid case object should be returned
    assert case_obj.internal_id == case_id


def test_resolve_report_case(click_context, caplog):
    """Tests error raise when an incorrect case ID is provided"""

    # GIVEN a delivery report click context

    # WHEN resolving an incorrect case ID, an exception should be raised
    with pytest.raises(click.exceptions.Abort):
        resolve_report_case(click_context, "not a case ID")

    assert "Invalid case ID" in caplog.text


def test_resolve_report_api(click_context, cg_context, case_id):
    """Tests report API extraction"""

    # GIVEN a case object
    case_obj = resolve_report_case(click_context, case_id)

    # WHEN retrieving a report API
    report_api = resolve_report_api(click_context, case_obj)

    # THEN the extracted API should be correctly retrieved
    assert report_api
    assert isinstance(report_api, MockMipDNAReportAPI)


def test_resolve_report_api_pipeline(click_context):
    """Tests API assignment given a specific pipeline"""

    # GIVEN a click context and a specific pipeline
    pipeline = Pipeline.BALSAMIC_UMI

    # WHEN validating a report api
    report_api = resolve_report_api_pipeline(click_context, pipeline)

    # THEN the extracted API should match the expected type
    assert report_api
    assert isinstance(report_api, BalsamicUmiReportAPI)


def test_resolve_report_analysis_started(click_context, case_id):
    """Tests retrieval of analysis started at field"""

    # GIVEN a case object and a report api
    case_obj = resolve_report_case(click_context, case_id)
    report_api = resolve_report_api(click_context, case_obj)

    # WHEN resolving the analysis started at field
    started_at = resolve_report_analysis_started(case_obj, report_api, None)

    # THEN check if the verified value has been correctly extracted and formatted
    assert started_at
    assert isinstance(started_at, datetime)
