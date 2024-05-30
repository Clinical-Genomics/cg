import pytest

from pathlib import Path

from cg.constants import Workflow, DataDelivery
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="failing_report_path")
def failing_report_path(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "fail_sars-cov-2_841080_results.csv")


@pytest.fixture(name="passing_report_path")
def passing_report_path(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "pass_sars-cov-2_208455_results.csv")


@pytest.fixture(name="mutant_store")
def mutant_store(cg_context: CGConfig) -> Store:
    return cg_context.status_db

