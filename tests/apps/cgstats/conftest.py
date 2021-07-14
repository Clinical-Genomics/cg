from pathlib import Path

import pytest

from cg.apps.cgstats.crud import create
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults
from tests.apps.demultiplex.conftest import *
from tests.models.demultiplexing.conftest import *


@pytest.fixture(name="stats_api")
def fixture_stats_api(project_dir: Path) -> StatsAPI:
    """Setup base CGStats store."""
    _store = StatsAPI({"cgstats": {"database": "sqlite://", "root": "tests/fixtures/DEMUX"}})
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.fixture(name="populated_stats_api")
def fixture_populated_stats_api(
    stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults
) -> StatsAPI:
    create.create_novaseq_flowcell(manager=stats_api, demux_results=bcl2fastq_demux_results)
    return stats_api


# vars(stats_api)
# {'config': {'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'SQLALCHEMY_BINDS': None, 'SQLALCHEMY_ECHO': False, 'SQLALCHEMY_POOL_SIZE': None, 'SQLALCHEMY_POOL_TIMEOUT': None, 'SQLALCHEMY_POOL_RECYCLE': None, 'SQLALCHEMY_MAX_OVERFLOW': None}, '_engines': {None: Engine(sqlite://)}, '_binds': {None: 'sqlite://'}, 'session_class': <class 'alchy.session.Session'>, 'session': <sqlalchemy.orm.scoping.scoped_session object at 0x7f4bdfcee3d0>, 'Model': <class 'alchy.model.Base'>, 'root_dir': PosixPath('tests/fixtures/DEMUX')}


@pytest.fixture(name="demultiplexing_stats_path")
def fixture_demultiplexing_stats_path(bcl2fastq_demux_results: DemuxResults) -> Path:
    return bcl2fastq_demux_results.demux_stats_path


@pytest.fixture(name="conversion_stats_path")
def fixture_conversion_stats_path(bcl2fastq_demux_results: DemuxResults) -> Path:
    return bcl2fastq_demux_results.conversion_stats_path
