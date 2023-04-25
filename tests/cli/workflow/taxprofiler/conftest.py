"""Fixtures for cli workflow taxprofiler tests"""

import datetime as dt
import gzip
from pathlib import Path
from typing import List

import pytest
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig

@pytest.fixture(scope="function", name="taxprofiler_context")
def fixture_taxprofiler_context(
    cg_context: CGConfig,
) -> CGConfig:
    """context to use in cli"""
    cg_context.meta_apis["analysis_api"] = TaxprofilerAnalysisAPI(config=cg_context)
    return cg_context
