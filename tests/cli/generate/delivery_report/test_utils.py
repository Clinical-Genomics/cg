"""Tests CLI utils for generating delivery reports."""

from datetime import datetime

import click.exceptions
import pytest

from cg.cli.generate.delivery_report.utils import (
    get_report_case,
    get_report_api,
    get_report_api_workflow,
    get_report_analysis_started_at,
)
from cg.constants import Workflow
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.store.models import Case


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


def test_get_report_analysis_started_at(
    raredisease_delivery_report_click_context: click.Context, raredisease_case_id: str
):
    """Tests retrieval of analysis started at field"""

    # GIVEN a case and a report api
    case: Case = get_report_case(
        context=raredisease_delivery_report_click_context, case_id=raredisease_case_id
    )
    report_api: DeliveryReportAPI = get_report_api(
        context=raredisease_delivery_report_click_context, case=case
    )

    # WHEN resolving the analysis started at field
    started_at = get_report_analysis_started_at(
        case=case, report_api=report_api, analysis_started_at=None
    )

    # THEN check if the verified value has been correctly extracted and formatted
    assert started_at
    assert isinstance(started_at, datetime)
