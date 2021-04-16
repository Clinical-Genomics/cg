from pathlib import Path

import pytest
from cg.apps.cgstats.stats import StatsAPI
from tests.apps.demultiplex.conftest import fixture_project_log


@pytest.fixture(name="stats_api")
def fixture_stats_api(project_dir: Path) -> StatsAPI:
    """Setup base CGStats store."""
    _store = StatsAPI({"cgstats": {"database": "sqlite://", "root": "tests/fixtures/DEMUX"}})
    _store.create_all()
    yield _store
    _store.drop_all()
