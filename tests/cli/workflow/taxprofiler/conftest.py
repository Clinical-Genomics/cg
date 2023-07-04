"""Fixtures for cli workflow taxprofiler tests"""

import pytest
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from pathlib import Path


@pytest.fixture(name="taxprofiler_dir")
def taxprofiler_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the taxprofiler apps dir."""
    taxprofiler_dir = tmpdir_factory.mktemp("taxprofiler")
    return Path(taxprofiler_dir).absolute().as_posix()


@pytest.fixture(scope="function", name="taxprofiler_context")
def fixture_taxprofiler_context(
    cg_context: CGConfig,
) -> CGConfig:
    """Context to use in cli."""
    cg_context.meta_apis["analysis_api"] = TaxprofilerAnalysisAPI(config=cg_context)
    return cg_context
