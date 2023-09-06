import pytest

from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store.api import Store
from cg.store.models import Sample, Family
from tests.store_helpers import StoreHelpers

FlowCellInfo = namedtuple("FlowCellInfo", "directory name sample_internal_ids")


@pytest.fixture(name="tmp_demulitplexing_dir")
def fixture_tmp_demulitplexing_dir(
    demultiplexed_runs: Path, bcl2fastq_flow_cell_full_name: str
) -> Path:
    """Return a tmp directory in demultiplexed-runs."""
    tmp_demulitplexing_dir: Path = Path(demultiplexed_runs, bcl2fastq_flow_cell_full_name)
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


@pytest.fixture(name="fastq_file_path")
def fixture_fastq_file_path() -> Path:
    """Return a path to a fastq file."""
    return Path("path/to/sample_internal_id_S1_L001_R1_001.fastq.gz")


@pytest.fixture(name="tmp_sample_sheet_path")
def fixture_tmp_samplesheet_path(tmp_demulitplexing_dir: Path) -> Path:
    """Return SampleSheet in temporary demuliplexing folder."""
    tmp_sample_sheet_path = Path(tmp_demulitplexing_dir, "SampleSheet.csv")
    with tmp_sample_sheet_path.open("w+") as fh:
        fh.write("content")
    return tmp_sample_sheet_path


@pytest.fixture(name="tmp_flow_cell_run_base_path")
def fixture_tmp_flow_cell_run_base_path(
    project_dir: Path, bcl2fastq_flow_cell_full_name: str
) -> Path:
    """Flow cell run directory in temporary folder."""

    tmp_flow_cell_run_path: Path = Path(project_dir, "flow_cells")
    tmp_flow_cell_run_path.mkdir(exist_ok=True, parents=True)

    return tmp_flow_cell_run_path


@pytest.fixture(name="tmp_flow_cell_demux_base_path")
def fixture_tmp_flow_cell_demux_base_path(
    project_dir: Path, bcl2fastq_flow_cell_full_name: str
) -> Path:
    """Flow cell demux directory in temporary folder."""

    tmp_flow_cell_demux_path: Path = Path(project_dir, "demultiplexed-runs")
    tmp_flow_cell_demux_path.mkdir(exist_ok=True, parents=True)

    return tmp_flow_cell_demux_path


@pytest.fixture(name="cgstats_select_project_log_file")
def fixture_cgstats_select_project_log_file(
    bcl2fastq_flow_cell: FlowCellDirectoryData, flow_cell_project_id: int
) -> Path:
    """Return cgstats select project out file."""
    return Path(
        bcl2fastq_flow_cell.path,
        "-".join(["stats", str(flow_cell_project_id), bcl2fastq_flow_cell.id]) + ".txt",
    )


@pytest.fixture(name="flow_cell_project_id")
def fixture_flow_cell_project_id() -> int:
    """Return flow cell run project id."""
    return 174578


@pytest.fixture(name="hiseq_x_copy_complete_file")
def fixture_hiseq_x_copy_complete_file(bcl2fastq_flow_cell: FlowCellDirectoryData) -> Path:
    """Return Hiseq X flow cell copy complete file."""
    return Path(bcl2fastq_flow_cell.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE)


@pytest.fixture(name="populated_flow_cell_store")
def fixture_populated_flow_cell_store(
    family_name: str,
    bcl2fastq_flow_cell_id: str,
    sample_id: str,
    store: Store,
    helpers: StoreHelpers,
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
        flow_cell_name=bcl2fastq_flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return populated_flow_cell_store


@pytest.fixture(name="active_flow_cell_store")
def fixture_active_flow_cell_store(
    family_name: str,
    bcl2fastq_flow_cell_id: str,
    sample_id: str,
    base_store: Store,
    helpers: StoreHelpers,
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
        flow_cell_name=bcl2fastq_flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return active_flow_cell_store


@pytest.fixture(name="sample_level_housekeeper_api")
def fixture_sample_level_housekeeper_api(
    bcl2fastq_flow_cell_id: str,
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
            {"path": path.as_posix(), "tags": ["fastq", bcl2fastq_flow_cell_id], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    helpers.ensure_hk_bundle(store=sample_level_housekeeper_api, bundle_data=bundle_data)
    return sample_level_housekeeper_api


@pytest.fixture(name="flow_cell_name_housekeeper_api")
def fixture_flow_cell_name_housekeeper_api(
    bcl2fastq_flow_cell_id: str,
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
            {"path": path.as_posix(), "tags": ["fastq", bcl2fastq_flow_cell_id], "archive": False}
            for path in tmp_fastq_paths
        ],
    }
    flow_cell_bundle_data = {
        "name": bcl2fastq_flow_cell_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": tmp_sample_sheet_path.as_posix(),
                "tags": ["samplesheet", bcl2fastq_flow_cell_id],
                "archive": False,
            }
        ],
    }

    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=bundle_data)
    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=flow_cell_bundle_data)
    return flow_cell_housekeeper_api


@pytest.fixture(name="populated_delete_demux_context")
def fixture_populated_delete_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    populated_flow_cell_store: Store,
    populated_stats_api: StatsAPI,
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    populated_delete_demux_context = cg_context
    populated_delete_demux_context.cg_stats_api_ = populated_stats_api
    populated_delete_demux_context.status_db_ = populated_flow_cell_store
    populated_delete_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    return populated_delete_demux_context


@pytest.fixture(name="populated_sample_lane_seq_demux_context")
def fixture_populated_sample_lane_seq_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    store_with_sequencing_metrics: Store,
    populated_stats_api: StatsAPI,
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    populated_wipe_demux_context = cg_context
    populated_wipe_demux_context.status_db_ = store_with_sequencing_metrics
    populated_wipe_demux_context.cg_stats_api_ = populated_stats_api
    populated_wipe_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    return populated_wipe_demux_context


@pytest.fixture(name="active_delete_demux_context")
def fixture_active_delete_demux_context(
    cg_context: CGConfig, active_flow_cell_store: Store, tmp_flow_cell_run_base_path: Path
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    active_delete_demux_context = cg_context
    active_delete_demux_context.status_db_ = active_flow_cell_store
    active_delete_demux_context.demultiplex_api.flow_cells_dir = tmp_flow_cell_run_base_path
    active_delete_demux_context.demultiplex_api.demultiplexed_runs_dir = tmp_flow_cell_run_base_path
    return active_delete_demux_context


@pytest.fixture(name="populated_delete_demultiplex_api")
def fixture_populated_delete_demultiplex_api(
    populated_delete_demux_context: CGConfig,
    bcl2fastq_flow_cell_id: str,
    tmp_flow_cell_run_base_path: Path,
    tmp_flow_cell_demux_base_path: Path,
) -> DeleteDemuxAPI:
    """Return an initialized populated DeleteDemuxAPI."""
    populated_delete_demux_context.demultiplex_api.flow_cells_dir = tmp_flow_cell_run_base_path
    populated_delete_demux_context.demultiplex_api.demultiplexed_runs_dir = (
        tmp_flow_cell_demux_base_path
    )
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    Path(tmp_flow_cell_demux_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    return DeleteDemuxAPI(
        config=populated_delete_demux_context,
        flow_cell_name=bcl2fastq_flow_cell_id,
        dry_run=False,
    )


@pytest.fixture(name="populated_sample_lane_sequencing_metrics_demultiplex_api")
def fixture_populated_sample_lane_sequencing_metrics_demultiplex_api(
    populated_sample_lane_seq_demux_context: CGConfig, bcl2fastq_flow_cell_id
) -> DeleteDemuxAPI:
    """Return an initialized populated DeleteDemuxAPI."""
    return DeleteDemuxAPI(
        config=populated_sample_lane_seq_demux_context,
        dry_run=False,
        flow_cell_name=bcl2fastq_flow_cell_id,
    )


@pytest.fixture(name="active_delete_demultiplex_api")
def fixture_active_delete_demultiplex_api(
    active_delete_demux_context: CGConfig,
    bcl2fastq_flow_cell_id: str,
    tmp_flow_cell_run_base_path: Path,
) -> DeleteDemuxAPI:
    """Return an instantiated DeleteDemuxAPI with active samples on a flow cell."""
    active_delete_demux_context.demultiplex_api.flow_cells_dir = tmp_flow_cell_run_base_path
    active_delete_demux_context.demultiplex_api.demultiplexed_runs_dir = tmp_flow_cell_run_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    return DeleteDemuxAPI(
        config=active_delete_demux_context,
        flow_cell_name=bcl2fastq_flow_cell_id,
        dry_run=False,
    )


@pytest.fixture(name="delete_demultiplex_api")
def fixture_delete_demultiplex_api(
    cg_context: CGConfig,
    bcl2fastq_flow_cell_id: str,
    stats_api: StatsAPI,
    tmp_flow_cell_run_base_path: Path,
) -> DeleteDemuxAPI:
    """Return an initialized DeleteDemuxAPI."""
    cg_context.cg_stats_api_ = stats_api
    cg_context.demultiplex_api.flow_cells_dir = tmp_flow_cell_run_base_path
    cg_context.demultiplex_api.demultiplexed_runs_dir = tmp_flow_cell_run_base_path
    Path(tmp_flow_cell_run_base_path, f"some_prefix_1100_{bcl2fastq_flow_cell_id}").mkdir(
        parents=True, exist_ok=True
    )
    return DeleteDemuxAPI(
        config=cg_context,
        dry_run=False,
        flow_cell_name=bcl2fastq_flow_cell_id,
    )


@pytest.fixture(name="flow_cell_info_map", scope="session")
def fixture_flow_cell_info_map(
    bcl_convert_demultiplexed_flow_cell_sample_internal_ids: List[str],
    bcl2fastq_demultiplexed_flow_cell_sample_internal_ids: List[str],
    flow_cell_directory_name_demultiplexed_with_bcl_convert_flat: Path,
    flow_cell_directory_name_demultiplexed_with_bcl_convert: Path,
    flow_cell_directory_name_demultiplexed_with_bcl_convert_on_sequencer: Path,
    flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer: str,
    flow_cell_name_demultiplexed_with_bcl_convert: str,
    flow_cell_directory_name_demultiplexed_with_bcl2fastq: Path,
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
) -> Dict[str, FlowCellInfo]:
    """Returns a dict with the suitable fixtures for different demultiplexing softwares and
    settings. Keys are string, values are named tuples FlowCellInfo."""
    return {
        "BCL2FASTQ_TREE": FlowCellInfo(
            directory=flow_cell_directory_name_demultiplexed_with_bcl2fastq,
            name=flow_cell_name_demultiplexed_with_bcl2fastq,
            sample_internal_ids=bcl2fastq_demultiplexed_flow_cell_sample_internal_ids,
        ),
        "BCLCONVERT_FLAT": FlowCellInfo(
            directory=flow_cell_directory_name_demultiplexed_with_bcl_convert_flat,
            name=flow_cell_name_demultiplexed_with_bcl_convert,
            sample_internal_ids=bcl_convert_demultiplexed_flow_cell_sample_internal_ids,
        ),
        "BCLCONVERT_TREE": FlowCellInfo(
            directory=flow_cell_directory_name_demultiplexed_with_bcl_convert,
            name=flow_cell_name_demultiplexed_with_bcl_convert,
            sample_internal_ids=bcl_convert_demultiplexed_flow_cell_sample_internal_ids,
        ),
        "BCLCONVERT_ON_SEQUENCER": FlowCellInfo(
            directory=flow_cell_directory_name_demultiplexed_with_bcl_convert_on_sequencer,
            name=flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer,
            sample_internal_ids=bcl_convert_demultiplexed_flow_cell_sample_internal_ids,
        ),
    }


@pytest.fixture(name="flow_cell_name_demultiplexed_with_bcl_convert", scope="session")
def fixture_flow_cell_name_demultiplexed_with_bcl_convert() -> str:
    return "HY7FFDRX2"


@pytest.fixture(name="flow_cell_directory_name_demultiplexed_with_bcl_convert", scope="session")
def fixture_flow_cell_directory_name_demultiplexed_with_bcl_convert(
    flow_cell_name_demultiplexed_with_bcl_convert: str,
):
    return f"230504_A00689_0804_B{flow_cell_name_demultiplexed_with_bcl_convert}"


@pytest.fixture(
    name="flow_cell_directory_name_demultiplexed_with_bcl_convert_flat", scope="session"
)
def fixture_flow_cell_directory_name_demultiplexed_with_bcl_convert_flat(
    flow_cell_name_demultiplexed_with_bcl_convert: str,
):
    """Return the name of a flow cell directory that has been demultiplexed with Bcl Convert using a flat output directory structure."""
    return f"230505_A00689_0804_B{flow_cell_name_demultiplexed_with_bcl_convert}"


@pytest.fixture(
    name="flow_cell_directory_name_demultiplexed_with_bcl_convert_on_sequencer", scope="session"
)
def fixture_flow_cell_directory_name_demultiplexed_with_bcl_convert_on_sequenver(
    flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer: str,
):
    """Return the name of a flow cell directory that has been demultiplexed with Bcl Convert on the NovaseqX sequencer."""
    return f"20230508_LH00188_0003_A{flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer}"


@pytest.fixture(name="flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer", scope="session")
def fixture_flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer() -> str:
    """Return the name of a flow cell directory that has been demultiplexed with Bcl Convert on the NovaseqX sequencer."""
    return "22522YLT3"


@pytest.fixture(name="demultiplexing_init_files")
def tmp_demultiplexing_init_files(
    bcl2fastq_flow_cell_id: str, populated_delete_demultiplex_api: DeleteDemuxAPI
) -> List[Path]:
    """Return a list of demultiplexing init files present in the run directory."""
    run_path: Path = populated_delete_demultiplex_api.run_path
    slurm_job_id_file_path: Path = Path(run_path, "slurm_job_ids.yaml")
    demux_script_file_path: Path = Path(run_path, "demux-novaseq.sh")
    error_log_path: Path = Path(run_path, f"{bcl2fastq_flow_cell_id}_demultiplex.stderr")
    log_path: Path = Path(run_path, f"{bcl2fastq_flow_cell_id}_demultiplex.stdout")

    demultiplexing_init_files: List[Path] = [
        slurm_job_id_file_path,
        demux_script_file_path,
        error_log_path,
        log_path,
    ]

    for file in demultiplexing_init_files:
        file.touch()
    return demultiplexing_init_files
