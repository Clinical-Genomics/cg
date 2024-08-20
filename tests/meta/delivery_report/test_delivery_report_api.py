"""Tests for the delivery report API."""

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants import Workflow
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.store.models import Case


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE])
def test_get_delivery_report_html(request: FixtureRequest, workflow: Workflow):
    """Test rendering of the delivery report for different workflows."""

    # GIVEN a delivery report API and a case object
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    delivery_report_html: str = delivery_report_api.get_delivery_report_html(
        case_id=case_id, analysis_date=case.analyses[0].started_at, force=False
    )
