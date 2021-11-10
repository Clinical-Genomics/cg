from datetime import datetime
from pathlib import Path
from typing import List, Generator

import pytest

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.demultiplex.wipe_demultiplex_api import WipeDemuxAPI
from cg.models.cg_config import CGConfig
from cg.store.api import Store
from cg.store.models import Sample
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="tmp_demulitplexing_dir")
def fixture_tmp_demulitplexing_dir(
    demultiplexed_flowcells_working_directory: Path, flowcell_full_name: str
) -> Generator[Path, None, None]:
    """Return a tmp directory in demultiplexed-runs"""
    tmp_demulitplexing_dir: Path = demultiplexed_flowcells_working_directory / flowcell_full_name
    tmp_demulitplexing_dir.mkdir(exist_ok=True, parents=True)
    yield tmp_demulitplexing_dir


@pytest.fixture(name="tmp_fastq_paths")
def fixture_temp_fastq_paths(tmp_path: Path) -> List[Path]:
    """Return a list of temporary dummy fastq paths"""
    fastq_1 = tmp_path / "fastq_1.fastq.gz"
    fastq_2 = tmp_path / "fastq_2.fastq.gz"

    fastqs = [fastq_1, fastq_2]
    for fastq in fastqs:
        with fastq.open("w+") as fh:
            fh.write("content")
    return fastqs


@pytest.fixture(name="tmp_sample_sheet_path")
def fixture_tmp_samplesheet_path(
    tmp_path: Path, flow_cell_name: str
) -> Generator[Path, None, None]:
    tmp_sample_sheet_path = tmp_path / "SampleSheet.csv"

    with tmp_sample_sheet_path.open("w+") as fh:
        fh.write("content")
    yield tmp_sample_sheet_path


@pytest.fixture(scope="function", name="populated_flow_cell_store")
def fixture_populated_flow_cell_store(
    family_name: str, flow_cell_name: str, helpers: StoreHelpers, sample_id: str, store: Store
) -> Store:
    """Populate a store with a novaseq flow cell"""
    populated_flow_cell_store: Store = store
    sample: Sample = helpers.add_sample(
        store=populated_flow_cell_store, sample_id=sample_id, internal_id=sample_id
    )
    helpers.add_case(store=populated_flow_cell_store, case_id=family_name, internal_id=family_name)
    helpers.add_relationship(
        store=populated_flow_cell_store,
        sample=store.sample(internal_id=sample_id),
        case=store.family(internal_id=family_name),
    )
    helpers.add_flowcell(
        store=populated_flow_cell_store,
        flowcell_id=flow_cell_name,
        sequencer_type="novaseq",
        samples=[sample],
    )
    yield populated_flow_cell_store


@pytest.fixture(scope="function", name="active_flow_cell_store")
def fixture_active_flow_cell_store(
    case_id: str,
    family_name: str,
    flow_cell_name: str,
    helpers: StoreHelpers,
    sample_id: str,
    base_store: Store,
) -> Store:
    """Populate a store with a novaseq flow cell, with active samples on it"""
    active_flow_cell_store: Store = base_store
    sample: Sample = helpers.add_sample(
        store=active_flow_cell_store, sample_id=sample_id, internal_id=sample_id
    )
    helpers.add_case(
        store=active_flow_cell_store, case_id=family_name, internal_id=family_name, action="running"
    )
    helpers.add_relationship(
        store=active_flow_cell_store,
        sample=active_flow_cell_store.sample(internal_id=sample_id),
        case=active_flow_cell_store.family(internal_id=family_name),
    )
    helpers.add_flowcell(
        store=active_flow_cell_store,
        flowcell_id=flow_cell_name,
        sequencer_type="novaseq",
        samples=[sample],
    )
    yield active_flow_cell_store


@pytest.fixture(scope="function", name="sample_level_housekeeper_api")
def fixture_sample_level_housekeeper_api(
    flow_cell_name: str,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
    tmp_sample_sheet_path: Path,
) -> Generator[HousekeeperAPI, None, None]:
    """Yield a mocked housekeeper API, containing a sample bundle with related fastq files"""
    sample_level_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq"], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    helpers.ensure_hk_bundle(store=sample_level_housekeeper_api, bundle_data=bundle_data)
    yield sample_level_housekeeper_api


@pytest.fixture(scope="function", name="flow_cell_name_housekeeper_api")
def fixture_flow_cell_name_housekeeper_api(
    flow_cell_name: str,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
    tmp_sample_sheet_path: Path,
) -> Generator[HousekeeperAPI, None, None]:
    """Yield a mocked housekeeper API, containing a sample bundle with related fastq files"""
    flow_cell_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq", flow_cell_name], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    flow_cell_bundle_data = {
        "name": flow_cell_name,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": tmp_sample_sheet_path.as_posix(),
                "tags": ["samplesheet", flow_cell_name],
                "archive": False,
            }
        ],
    }

    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=bundle_data)
    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=flow_cell_bundle_data)
    yield flow_cell_housekeeper_api


@pytest.fixture(scope="function", name="populated_wipe_demux_context")
def fixture_populated_wipe_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    populated_flow_cell_store: Store,
    populated_stats_api: StatsAPI,
) -> Generator[CGConfig, None, None]:
    """Yield a populated context to remove flowcells from using the WipeDemuxAPI"""
    populated_wipe_demux_context = cg_context
    populated_wipe_demux_context.cg_stats_api_ = populated_stats_api
    populated_wipe_demux_context.status_db_ = populated_flow_cell_store
    populated_wipe_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    yield populated_wipe_demux_context


@pytest.fixture(scope="function", name="active_wipe_demux_context")
def fixture_active_wipe_demux_context(
    cg_context: CGConfig, active_flow_cell_store: Store
) -> Generator[CGConfig, None, None]:
    """Yield a populated context to remove flowcells from using the WipeDemuxAPI"""
    active_wipe_demux_context = cg_context
    active_wipe_demux_context.status_db_ = active_flow_cell_store
    yield active_wipe_demux_context


@pytest.fixture(scope="function", name="populated_wipe_demultiplex_api")
def fixture_populated_wipe_demultiplex_api(
    populated_wipe_demux_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
    stats_api: StatsAPI,
) -> Generator[WipeDemuxAPI, None, None]:
    """Yield an initialized populated WipeDemuxAPI"""
    populated_wipe_demultiplex_api: WipeDemuxAPI = WipeDemuxAPI(
        config=populated_wipe_demux_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )

    yield populated_wipe_demultiplex_api


@pytest.fixture(scope="function", name="active_wipe_demultiplex_api")
def fixture_active_wipe_demultiplex_api(
    active_wipe_demux_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
) -> Generator[WipeDemuxAPI, None, None]:
    """Yield an instantiated WipeDemuxAPI with active samples on a flowcell"""
    active_wipe_demultiplex_api = WipeDemuxAPI(
        config=active_wipe_demux_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )
    yield active_wipe_demultiplex_api


@pytest.fixture(scope="function", name="wipe_demultiplex_api")
def fixture_wipe_demultiplex_api(
    cg_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
    stats_api: StatsAPI,
) -> Generator[WipeDemuxAPI, None, None]:
    """Yield an initialized WipeDemuxAPI"""
    cg_context.cg_stats_api_ = stats_api
    wipe_demux_api: WipeDemuxAPI = WipeDemuxAPI(
        config=cg_context,
        demultiplexing_dir=demultiplexed_flowcells_working_directory,
        run_name=flowcell_full_name,
    )
    yield wipe_demux_api
