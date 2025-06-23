"""Tests CLI utils for generating delivery reports."""

from datetime import datetime
from unittest.mock import create_autospec

import click.exceptions
import pytest

from cg.cli.generate.delivery_report.utils import (
    get_analysis_for_delivery_report,
    get_report_api,
    get_report_api_workflow,
    get_report_case,
)
from cg.constants import Workflow
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.store.models import Analysis, Case


def test_get_report_case(
    raredisease_delivery_report_click_context: click.Context, raredisease_case_id: str
):
    """Tests case object extraction for delivery report generation given a valid case ID."""

    # GIVEN a delivery report click context

    # WHEN resolving a report case ID
    case: Case = get_report_case(
        context=raredisease_delivery_report_click_context, case_id=raredisease_case_id
    )

    # THEN a valid case should be returned
    assert case.internal_id == raredisease_case_id


def test_get_report_case_invalid_case_id(
    raredisease_delivery_report_click_context: click.Context, case_id_does_not_exist: str, caplog
):
    """Tests error raise when an incorrect case ID is provided."""

    # GIVEN a delivery report click context

    # WHEN resolving an invalid report case ID

    # THEN an exception should be raised
    with pytest.raises(click.exceptions.Abort):
        get_report_case(
            context=raredisease_delivery_report_click_context, case_id=case_id_does_not_exist
        )


def test_get_report_api(
    raredisease_delivery_report_click_context: click.Context, raredisease_case_id: str
):
    """Tests delivery report API extraction."""

    # GIVEN a case
    case: Case = get_report_case(
        context=raredisease_delivery_report_click_context, case_id=raredisease_case_id
    )

    # WHEN retrieving a report API
    report_api: DeliveryReportAPI = get_report_api(
        context=raredisease_delivery_report_click_context, case=case
    )

    # THEN the extracted API should be correctly retrieved
    assert report_api
    assert isinstance(report_api, RarediseaseDeliveryReportAPI)


def test_get_report_api_workflow(raredisease_delivery_report_click_context: click.Context):
    """Tests API assignment given a specific workflow."""

    # GIVEN a click context and a specific workflow

    # WHEN validating a report api
    report_api = get_report_api_workflow(
        context=raredisease_delivery_report_click_context, workflow=Workflow.RAREDISEASE
    )

    # THEN the extracted API should match the expected type
    assert report_api
    assert isinstance(report_api, RarediseaseDeliveryReportAPI)


def test_get_analysis_for_delivery_report(
    raredisease_delivery_report_click_context: click.Context, raredisease_case_id: str
):
    """Tests retrieval of analysis completed at field"""

    # GIVEN a case
    case: Case = get_report_case(
        context=raredisease_delivery_report_click_context, case_id=raredisease_case_id
    )

    # GIVEN a completed analysis linked to the case
    analysis: Analysis = create_autospec(Analysis)
    analysis.completed_at = datetime.now()
    analysis.housekeeper_version_id = 1234
    analysis.case = case

    # WHEN getting the analysis for delivery report
    analysis: Analysis = get_analysis_for_delivery_report(case)

    # THEN an analysis is returned
    assert isinstance(analysis, Analysis)


def test_get_analysis_for_delivery_report_no_completed_analysis(
    raredisease_delivery_report_click_context: click.Context, raredisease_case_id: str
):
    """Tests error raise when no completed analysis is found for the case."""

    # GIVEN a case with no completed analysis
    case: Case = get_report_case(
        context=raredisease_delivery_report_click_context, case_id=raredisease_case_id
    )
    case.analyses[0].completed_at = None

    # WHEN getting the analysis for delivery report

    # THEN an exception should be raised
    with pytest.raises(click.exceptions.Abort):
        get_analysis_for_delivery_report(case)
