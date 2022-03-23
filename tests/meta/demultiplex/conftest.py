import pytest

from datetime import datetime
from pathlib import Path
from typing import List

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.store.api import Store
from cg.store.models import Sample, Family

from tests.apps.cgstats.conftest import fixture_populated_stats_api
from tests.cli.demultiplex.conftest import (
    fixture_demultiplex_configs,
    fixture_demultiplex_context,
    fixture_demultiplexed_flowcell_working_directory,
    fixture_demultiplexed_flowcells_working_directory,
    fixture_demultiplexing_api,
    fixture_demux_results_not_finished_dir,
    fixture_demux_run_dir,
    fixture_flowcell_object,
    fixture_flowcell_runs_working_directory,
    fixture_sbatch_process,
    fixture_stats_api,
)
from tests.models.demultiplexing.conftest import (
    fixture_bcl2fastq_demux_results,
    fixture_demultiplexed_flowcell,
    fixture_demultiplexed_runs,
    fixture_flowcell_object,
    fixture_flowcell_path,
    fixture_flowcell_runs,
)


@pytest.fixture(name="tmp_demulitplexing_dir")
def fixture_tmp_demulitplexing_dir(
    demultiplexed_flowcells_working_directory: Path, flowcell_full_name: str
) -> Path:
    """Return a tmp directory in demultiplexed-runs"""
    tmp_demulitplexing_dir: Path = demultiplexed_flowcells_working_directory / flowcell_full_name
    tmp_demulitplexing_dir.mkdir(exist_ok=True, parents=True)
    return tmp_demulitplexing_dir


@pytest.fixture(name="tmp_fastq_paths")
def fixture_temp_fastq_paths(tmp_demulitplexing_dir: Path) -> List[Path]:
    """Return a list of temporary dummy fastq paths"""
    fastq_1 = tmp_demulitplexing_dir / "fastq_1.fastq.gz"
    fastq_2 = tmp_demulitplexing_dir / "fastq_2.fastq.gz"

    fastqs = [fastq_1, fastq_2]
    for fastq in fastqs:
        with fastq.open("w+") as fh:
            fh.write("content")
    return fastqs


@pytest.fixture(name="tmp_sample_sheet_path")
def fixture_tmp_samplesheet_path(tmp_demulitplexing_dir: Path) -> Path:
    """SampleSheet in temporary folder"""
    tmp_sample_sheet_path = tmp_demulitplexing_dir / "SampleSheet.csv"

    with tmp_sample_sheet_path.open("w+") as fh:
        fh.write("content")
    return tmp_sample_sheet_path


@pytest.fixture(name="tmp_flow_cell_run_path")
def fixture_tmp_flow_cell_run_path(project_dir: Path, flowcell_full_name: str) -> Path:
    """Flow cell run directory in temporary folder"""

    tmp_flow_cell_run_path = project_dir / Path("flow_cell_run") / flowcell_full_name

    tmp_flow_cell_run_path.mkdir(exist_ok=True, parents=True)

    return tmp_flow_cell_run_path


@pytest.fixture(scope="function", name="populated_flow_cell_store")
def fixture_populated_flow_cell_store(
    family_name: str, flowcell_name: str, sample_id: str, store: Store, helpers
) -> Store:
    """Populate a store with a novaseq flow cell"""
    populated_flow_cell_store: Store = store
    sample: Sample = helpers.add_sample(store=populated_flow_cell_store, internal_id=sample_id)
    family: Family = helpers.add_case(store=populated_flow_cell_store, internal_id=family_name)
    helpers.add_relationship(
        store=populated_flow_cell_store,
        sample=sample,
        case=family,
    )
    helpers.add_flowcell(
        store=populated_flow_cell_store,
        flowcell_id=flowcell_name,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return populated_flow_cell_store


@pytest.fixture(scope="function", name="active_flow_cell_store")
def fixture_active_flow_cell_store(
    family_name: str, flowcell_name: str, sample_id: str, base_store: Store, helpers
) -> Store:
    """Populate a store with a novaseq flow cell, with active samples on it"""
    active_flow_cell_store: Store = base_store
    sample: Sample = helpers.add_sample(store=active_flow_cell_store, internal_id=sample_id)
    family: Family = helpers.add_case(
        store=active_flow_cell_store, internal_id=family_name, action="running"
    )
    helpers.add_relationship(
        store=active_flow_cell_store,
        sample=sample,
        case=family,
    )
    helpers.add_flowcell(
        store=active_flow_cell_store,
        flowcell_id=flowcell_name,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return active_flow_cell_store


@pytest.fixture(scope="function", name="sample_level_housekeeper_api")
def fixture_sample_level_housekeeper_api(
    flowcell_name: str,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
    helpers,
) -> HousekeeperAPI:
    """Yield a mocked housekeeper API, containing a sample bundle with related fastq files"""
    sample_level_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq", flowcell_name], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    helpers.ensure_hk_bundle(store=sample_level_housekeeper_api, bundle_data=bundle_data)
    return sample_level_housekeeper_api


@pytest.fixture(scope="function", name="flow_cell_name_housekeeper_api")
def fixture_flow_cell_name_housekeeper_api(
    flowcell_name: str,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
    tmp_sample_sheet_path: Path,
    helpers,
) -> HousekeeperAPI:
    """Yield a mocked housekeeper API, containing a sample bundle with related fastq files"""
    flow_cell_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq", flowcell_name], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    flow_cell_bundle_data = {
        "name": flowcell_name,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": tmp_sample_sheet_path.as_posix(),
                "tags": ["samplesheet", flowcell_name],
                "archive": False,
            }
        ],
    }

    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=bundle_data)
    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=flow_cell_bundle_data)
    return flow_cell_housekeeper_api


@pytest.fixture(scope="function", name="populated_wipe_demux_context")
def fixture_populated_wipe_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    populated_flow_cell_store: Store,
    populated_stats_api: StatsAPI,
) -> CGConfig:
    """Yield a populated context to remove flowcells from using the DeleteDemuxAPI"""
    populated_wipe_demux_context = cg_context
    populated_wipe_demux_context.cg_stats_api_ = populated_stats_api
    populated_wipe_demux_context.status_db_ = populated_flow_cell_store
    populated_wipe_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    return populated_wipe_demux_context


@pytest.fixture(scope="function", name="active_wipe_demux_context")
def fixture_active_wipe_demux_context(
    cg_context: CGConfig, active_flow_cell_store: Store
) -> CGConfig:
    """Yield a populated context to remove flowcells from using the DeleteDemuxAPI"""
    active_wipe_demux_context = cg_context
    active_wipe_demux_context.status_db_ = active_flow_cell_store
    return active_wipe_demux_context


@pytest.fixture(scope="function", name="populated_wipe_demultiplex_api")
def fixture_populated_wipe_demultiplex_api(
    populated_wipe_demux_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    tmp_flow_cell_run_path: Path,
) -> DeleteDemuxAPI:
    """Yield an initialized populated DeleteDemuxAPI"""
    return DeleteDemuxAPI(
        config=populated_wipe_demux_context,
        demultiplex_base=demultiplexed_flowcells_working_directory,
        dry_run=False,
        run_path=tmp_flow_cell_run_path,
    )


@pytest.fixture(scope="function", name="active_wipe_demultiplex_api")
def fixture_active_wipe_demultiplex_api(
    active_wipe_demux_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
) -> DeleteDemuxAPI:
    """Yield an instantiated DeleteDemuxAPI with active samples on a flowcell"""
    return DeleteDemuxAPI(
        config=active_wipe_demux_context,
        demultiplex_base=demultiplexed_flowcells_working_directory,
        dry_run=False,
        run_path=Path(flowcell_full_name),
    )


@pytest.fixture(scope="function", name="wipe_demultiplex_api")
def fixture_wipe_demultiplex_api(
    cg_context: CGConfig,
    demultiplexed_flowcells_working_directory: Path,
    flowcell_full_name: str,
    stats_api: StatsAPI,
) -> DeleteDemuxAPI:
    """Yield an initialized DeleteDemuxAPI"""
    cg_context.cg_stats_api_ = stats_api
    return DeleteDemuxAPI(
        config=cg_context,
        demultiplex_base=demultiplexed_flowcells_working_directory,
        dry_run=False,
        run_path=Path(flowcell_full_name),
    )


@pytest.fixture(name="demultiplexing_init_files")
def tmp_demultiplexing_init_files(
    flowcell_name: str, populated_wipe_demultiplex_api: DeleteDemuxAPI
) -> List[Path]:
    """Return a list of demultiplexing init files present in the run directory"""
    run_path: Path = populated_wipe_demultiplex_api.run_path
    slurm_job_id_file_path: Path = run_path / "slurm_job_ids.yaml"
    demux_script_file_path: Path = run_path / "demux-novaseq.sh"
    error_log_path: Path = run_path / f"{flowcell_name}_demultiplex.stderr"
    log_path: Path = run_path / f"{flowcell_name}_demultiplex.stdout"

    demultiplexing_init_files: List[Path] = [
        slurm_job_id_file_path,
        demux_script_file_path,
        error_log_path,
        log_path,
    ]

    for file in demultiplexing_init_files:
        file.touch()

    return demultiplexing_init_files
