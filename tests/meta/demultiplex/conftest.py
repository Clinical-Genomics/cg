import pytest

from datetime import datetime
from pathlib import Path
from typing import List

from tests.cli.demultiplex.conftest import (
    fixture_bcl2fastq_demux_results,
    fixture_demultiplex_configs,
    fixture_demultiplex_context,
    fixture_demultiplex_fixtures,
    fixture_demultiplexed_flowcell,
    fixture_demultiplexed_flowcell_working_directory,
    fixture_demultiplexed_flowcells_working_directory,
    fixture_demultiplexing_api,
    fixture_demux_results_not_finished_dir,
    fixture_demux_run_dir,
    fixture_demultiplexed_runs,
    fixture_flowcell_full_name,
    fixture_flowcell_object,
    fixture_flowcell_full_name,
    fixture_flowcell_object,
    fixture_flowcell_runs_working_directory,
    fixture_sbatch_process,
)
from tests.apps.cgstats.conftest import fixture_stats_api, fixture_populated_stats_api
from tests.store.api.conftest import fixture_flow_cell_store
from tests.store_helpers import StoreHelpers

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.cgstats.stats import StatsAPI
from cg.meta.demultiplex.wipe_demultiplex_api import WipeDemuxAPI
from cg.models.cg_config import CGConfig
from cg.store.api import Store


@pytest.fixture(name="tmp_fastq_paths")
def fixture_temp_fastq_paths(tmp_path: Path, run_name: str) -> List[Path]:
    """Return a list of temporary dummy fastq paths"""
    fastq_1 = tmp_path / "fastq_1.fastq.gz"
    fastq_2 = tmp_path / "fastq_2.fastq.gz"

    fastqs = [fastq_1, fastq_2]
    for fastq in fastqs:
        with fastq.open("w+") as fh:
            fh.write("content")
    yield fastqs


@pytest.fixture(scope="function", name="flow_cell_housekeeper_api")
def fixture_flow_cell_housekeeper_api(
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
) -> HousekeeperAPI:
    """Yield a mocked housekeeper API, containing a sample bundle with related fastq files"""
    flow_cell_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq"], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=bundle_data)
    yield flow_cell_housekeeper_api


@pytest.fixture(scope="function", name="populated_wipe_demux_context")
def fixture_populated_wipe_demux_context(
    cg_context: CGConfig,
    flow_cell_housekeeper_api: HousekeeperAPI,
    flow_cell_store: Store,
    populated_stats_api: StatsAPI,
) -> CGConfig:
    """Yield a populated context to remove flowcells from using the WipeDemuxAPI"""
    populated_wipe_demux_context = cg_context
    populated_wipe_demux_context.cg_stats_api_ = populated_stats_api
    populated_wipe_demux_context.status_db_ = flow_cell_store
    populated_wipe_demux_context.housekeeper_api_ = flow_cell_housekeeper_api
    yield populated_wipe_demux_context


@pytest.fixture(scope="function", name="populated_wipe_demultiplex_api")
def fixture_populated_wipe_demultiplex_api(
    populated_wipe_demux_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
    stats_api: StatsAPI,
) -> WipeDemuxAPI:
    """Yield an initialized populated WipeDemuxAPI"""
    populated_wipe_demultiplex_api: WipeDemuxAPI = WipeDemuxAPI(
        config=populated_wipe_demux_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )
    yield populated_wipe_demultiplex_api


@pytest.fixture(scope="function", name="wipe_demultiplex_api")
def fixture_wipe_demultiplex_api(
    cg_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
    stats_api: StatsAPI,
) -> WipeDemuxAPI:
    """Yield an initialized WipeDemuxAPI"""
    cg_context.cg_stats_api_ = stats_api
    wipe_demux_api: WipeDemuxAPI = WipeDemuxAPI(
        config=cg_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )
    yield wipe_demux_api
