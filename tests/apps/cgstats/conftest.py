from pathlib import Path

import pytest
from cg.apps.cgstats.stats import StatsAPI
from tests.apps.demultiplex.conftest import fixture_demultiplex_fixtures
from tests.models.demultiplexing.conftest import (
    fixture_demultiplexed_flowcell,
    fixture_demultiplexed_runs,
    fixture_demux_results,
    fixture_flowcell_full_name,
    fixture_flowcell_object,
    fixture_flowcell_path,
    fixture_flowcell_runs,
)


@pytest.fixture(name="stats_api")
def fixture_stats_api(project_dir: Path) -> StatsAPI:
    """Setup base CGStats store."""
    _store = StatsAPI({"cgstats": {"database": "sqlite://", "root": "tests/fixtures/DEMUX"}})
    _store.create_all()
    yield _store
    _store.drop_all()
