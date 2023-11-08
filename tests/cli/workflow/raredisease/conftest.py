"""Fixtures for cli workflow raredisease tests"""

import pytest

from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig


@pytest.fixture(scope="function", name="raredisease_context")
def fixture_raredisease_context(
    cg_context: CGConfig,
) -> CGConfig:
    """Context to use in cli."""
    cg_context.meta_apis["analysis_api"] = RarediseaseAnalysisAPI(config=cg_context)
    return cg_context
