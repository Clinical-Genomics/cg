import pytest

from datetime import datetime
from pathlib import Path
from typing import List

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCell
from cg.store.api import Store
from cg.store.models import Sample, Family

from tests.apps.cgstats.conftest import fixture_populated_stats_api
from tests.cli.demultiplex.conftest import (
    fixture_demultiplex_configs,
    fixture_demultiplex_context,
    fixture_demultiplexed_flow_cell_working_directory,
    fixture_demultiplexed_flow_cells_working_directory,
    fixture_demultiplexing_api,
    fixture_demux_results_not_finished_dir,
    fixture_flow_cell_runs_working_directory,
    fixture_stats_api,
)
from tests.models.demultiplexing.conftest import (
    fixture_flowcell_path,
    fixture_flow_cell_runs,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="tmp_demulitplexing_dir")
def fixture_tmp_demulitplexing_dir(
    demultiplexed_flow_cells_working_directory: Path, flow_cell_full_name: str
) -> Path:
    """Return a tmp directory in demultiplexed-runs."""
    tmp_demulitplexing_dir: Path = Path(
        demultiplexed_flow_cells_working_directory, flow_cell_full_name
    )
    tmp_demulitplexing_dir.mkdir(exist_ok=True, parents=True)
    return tmp_demulitplexing_dir


@pytest.fixture(name="tmp_fastq_paths")
def fixture_temp_fastq_paths(tmp_demulitplexing_dir: Path) -> List[Path]:
    """Return a list of temporary dummy fastq paths."""
    fastqs = [
        Path(tmp_demulitplexing_dir, "fastq_1.fastq.gz"),
        Path(tmp_demulitplexing_dir, "fastq_2.fastq.gz"),
    ]
    for fastq in fastqs:
        with fastq.open("w+") as fh:
            fh.write("content")
    return fastqs


@pytest.fixture(name="tmp_sample_sheet_path")
def fixture_tmp_samplesheet_path(tmp_demulitplexing_dir: Path) -> Path:
    """Return SampleSheet in temporary demuliplexing folder."""
    tmp_sample_sheet_path = Path(tmp_demulitplexing_dir, "SampleSheet.csv")
    with tmp_sample_sheet_path.open("w+") as fh:
        fh.write("content")
    return tmp_sample_sheet_path


@pytest.fixture(name="tmp_flow_cell_run_path")
def fixture_tmp_flow_cell_run_path(project_dir: Path, flow_cell_full_name: str) -> Path:
    """Flow cell run directory in temporary folder."""

    tmp_flow_cell_run_path: Path = Path(project_dir, "flow_cell_run", flow_cell_full_name)
    tmp_flow_cell_run_path.mkdir(exist_ok=True, parents=True)

    return tmp_flow_cell_run_path


@pytest.fixture(name="cgstats_select_project_log_file")
def fixture_cgstats_select_project_log_file(flow_cell: FlowCell, flow_cell_project_id: int) -> Path:
    """Return cgstats select project out file."""
    return Path(
        flow_cell.path,
        "-".join(["stats", str(flow_cell_project_id), flow_cell.id]) + ".txt",
    )


@pytest.fixture(name="flow_cell_project_id")
def fixture_flow_cell_project_id() -> int:
    """Return flow cell run project id."""
    return 174578


@pytest.fixture(name="hiseq_x_copy_complete_file")
def fixture_hiseq_x_copy_complete_file(flow_cell: FlowCell) -> Path:
    """Return Hiseq X flow cell copy complete file."""
    return Path(flow_cell.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE)


@pytest.fixture(name="populated_flow_cell_store")
def fixture_populated_flow_cell_store(
    family_name: str, flow_cell_id: str, sample_id: str, store: Store, helpers: StoreHelpers
) -> Store:
    """Populate a store with a NovaSeq flow cell."""

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
        flow_cell_id=flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return populated_flow_cell_store


@pytest.fixture(name="active_flow_cell_store")
def fixture_active_flow_cell_store(
    family_name: str, flow_cell_id: str, sample_id: str, base_store: Store, helpers: StoreHelpers
) -> Store:
    """Populate a store with a Novaseq flow cell, with active samples on it."""
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
        flow_cell_id=flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return active_flow_cell_store


@pytest.fixture(name="sample_level_housekeeper_api")
def fixture_sample_level_housekeeper_api(
    flow_cell_id: str,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
    helpers,
) -> HousekeeperAPI:
    """Return a mocked Housekeeper API, containing a sample bundle with related FASTQ files."""
    sample_level_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq", flow_cell_id], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    helpers.ensure_hk_bundle(store=sample_level_housekeeper_api, bundle_data=bundle_data)
    return sample_level_housekeeper_api


@pytest.fixture(name="flow_cell_name_housekeeper_api")
def fixture_flow_cell_name_housekeeper_api(
    flow_cell_id: str,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: List[Path],
    tmp_sample_sheet_path: Path,
    helpers,
) -> HousekeeperAPI:
    """Return a mocked Housekeeper API, containing a sample bundle with related FASTQ files."""
    flow_cell_housekeeper_api = real_housekeeper_api
    bundle_data = {
        "name": sample_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {"path": path.as_posix(), "tags": ["fastq", flow_cell_id], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    flow_cell_bundle_data = {
        "name": flow_cell_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": tmp_sample_sheet_path.as_posix(),
                "tags": ["samplesheet", flow_cell_id],
                "archive": False,
            }
        ],
    }

    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=bundle_data)
    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=flow_cell_bundle_data)
    return flow_cell_housekeeper_api


@pytest.fixture(name="populated_wipe_demux_context")
def fixture_populated_wipe_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    populated_flow_cell_store: Store,
    populated_stats_api: StatsAPI,
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    populated_wipe_demux_context = cg_context
    populated_wipe_demux_context.cg_stats_api_ = populated_stats_api
    populated_wipe_demux_context.status_db_ = populated_flow_cell_store
    populated_wipe_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    return populated_wipe_demux_context


@pytest.fixture(name="active_wipe_demux_context")
def fixture_active_wipe_demux_context(
    cg_context: CGConfig, active_flow_cell_store: Store
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    active_wipe_demux_context = cg_context
    active_wipe_demux_context.status_db_ = active_flow_cell_store
    return active_wipe_demux_context


@pytest.fixture(name="populated_wipe_demultiplex_api")
def fixture_populated_wipe_demultiplex_api(
    populated_wipe_demux_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    tmp_flow_cell_run_path: Path,
) -> DeleteDemuxAPI:
    """Return an initialized populated DeleteDemuxAPI."""
    return DeleteDemuxAPI(
        config=populated_wipe_demux_context,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=False,
        run_path=tmp_flow_cell_run_path,
    )


@pytest.fixture(name="active_wipe_demultiplex_api")
def fixture_active_wipe_demultiplex_api(
    active_wipe_demux_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    flow_cell_full_name: str,
) -> DeleteDemuxAPI:
    """Return an instantiated DeleteDemuxAPI with active samples on a flow cell."""
    return DeleteDemuxAPI(
        config=active_wipe_demux_context,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=False,
        run_path=Path(flow_cell_full_name),
    )


@pytest.fixture(name="wipe_demultiplex_api")
def fixture_wipe_demultiplex_api(
    cg_context: CGConfig,
    demultiplexed_flow_cells_working_directory: Path,
    flow_cell_full_name: str,
    stats_api: StatsAPI,
) -> DeleteDemuxAPI:
    """Return an initialized DeleteDemuxAPI."""
    cg_context.cg_stats_api_ = stats_api
    return DeleteDemuxAPI(
        config=cg_context,
        demultiplex_base=demultiplexed_flow_cells_working_directory,
        dry_run=False,
        run_path=Path(flow_cell_full_name),
    )


@pytest.fixture(name="demultiplexing_init_files")
def tmp_demultiplexing_init_files(
    flow_cell_id: str, populated_wipe_demultiplex_api: DeleteDemuxAPI
) -> List[Path]:
    """Return a list of demultiplexing init files present in the run directory."""
    run_path: Path = populated_wipe_demultiplex_api.run_path
    slurm_job_id_file_path: Path = Path(run_path, "slurm_job_ids.yaml")
    demux_script_file_path: Path = Path(run_path, "demux-novaseq.sh")
    error_log_path: Path = Path(run_path, f"{flow_cell_id}_demultiplex.stderr")
    log_path: Path = Path(run_path, f"{flow_cell_id}_demultiplex.stdout")

    demultiplexing_init_files: List[Path] = [
        slurm_job_id_file_path,
        demux_script_file_path,
        error_log_path,
        log_path,
    ]

    for file in demultiplexing_init_files:
        file.touch()
    return demultiplexing_init_files
