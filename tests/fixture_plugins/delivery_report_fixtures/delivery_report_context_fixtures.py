"""Delivery report CG context fixtures."""

import pytest

from cg.models.cg_config import CGConfig


@pytest.fixture
def raredisease_delivery_report_context(raredisease_context: CGConfig):
    """Raredisease context for the delivery report generation."""
    return raredisease_context


# cg_context.meta_apis["analysis_api"] = MockMipDNAAnalysisAPI(config=cg_context)
# cg_context.status_db_ = report_store
# cg_context.lims_api_ = MockLimsAPI(cg_context, lims_samples)
# cg_context.chanjo_api_ = MockChanjo()
# cg_context.scout_api_ = MockScoutApi(cg_context)
# return MockHousekeeperMipDNAReportAPI(cg_context, cg_context.meta_apis["analysis_api"])
