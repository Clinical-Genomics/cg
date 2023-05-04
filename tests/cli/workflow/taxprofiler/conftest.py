"""Fixtures for cli workflow taxprofiler tests"""

import pytest
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig


@pytest.fixture(scope="function", name="taxprofiler_context")
def fixture_taxprofiler_context(
    cg_context: CGConfig,
) -> CGConfig:
    """Context to use in cli."""
    cg_context.meta_apis["analysis_api"] = TaxprofilerAnalysisAPI(config=cg_context)
    return cg_context
