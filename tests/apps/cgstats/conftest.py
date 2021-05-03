from pathlib import Path

import pytest
from cg.apps.cgstats.crud import create
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults
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


@pytest.fixture(name="populated_stats_api")
def fixture_populated_stats_api(stats_api: StatsAPI, demux_results: DemuxResults) -> StatsAPI:
    create.create_novaseq_flowcell(manager=stats_api, demux_results=demux_results)
    return stats_api


@pytest.fixture(name="demultiplexing_stats_path")
def fixture_demultiplexing_stats_path(demux_results: DemuxResults) -> Path:
    return demux_results.demux_stats_path


@pytest.fixture(name="conversion_stats_path")
def fixture_conversion_stats_path(demux_results: DemuxResults) -> Path:
    return demux_results.conversion_stats_path
