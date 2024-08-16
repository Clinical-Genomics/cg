"""Delivery report API fixtures."""

import pytest

from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.models.cg_config import CGConfig


@pytest.fixture
def raredisease_delivery_report_api(
    raredisease_delivery_report_context: CGConfig,
) -> RarediseaseDeliveryReportAPI:
    """Rare disease delivery report API fixture."""
    return RarediseaseDeliveryReportAPI(
        config=raredisease_delivery_report_context,
        analysis_api=raredisease_delivery_report_context.meta_apis["analysis_api"],
    )
