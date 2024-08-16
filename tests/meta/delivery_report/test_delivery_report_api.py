"""Tests for the delivery report API."""

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants import Workflow
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE])
def test_get_delivery_report_html(request: FixtureRequest, workflow: Workflow):
    """Test rendering of the delivery report for different workflows."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow.replace('-', '_')}_delivery_report_api"
    )
