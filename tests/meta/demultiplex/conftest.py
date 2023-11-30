import os
import shutil
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_sample_sheet_path_to_housekeeper,
)
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.store.api import Store
from cg.store.models import Case, Sample
from tests.store_helpers import StoreHelpers

FlowCellInfo = namedtuple("FlowCellInfo", "directory name sample_internal_ids")


@pytest.fixture(name="tmp_demulitplexing_dir")
def tmp_demulitplexing_dir(demultiplexed_runs: Path, bcl2fastq_flow_cell_full_name: str) -> Path:
    """Return a tmp directory in demultiplexed-runs."""
    tmp_demulitplexing_dir: Path = Path(demultiplexed_runs, bcl2fastq_flow_cell_full_name)
    tmp_demulitplexing_dir.mkdir(exist_ok=True, parents=True)
    return tmp_demulitplexing_dir


@pytest.fixture(name="tmp_fastq_paths")
def temp_fastq_paths(tmp_demulitplexing_dir: Path) -> list[Path]:
    """Return a list of temporary dummy fastq paths."""
    fastqs = [
        Path(tmp_demulitplexing_dir, "fastq_1.fastq.gz"),
        Path(tmp_demulitplexing_dir, "fastq_2.fastq.gz"),
    ]
    for fastq in fastqs:
        with fastq.open("w+") as fh:
            fh.write("content")
    return fastqs


@pytest.fixture
def demultiplex_fastq_file_path() -> Path:
    """Return a path to non-existent a fastq file."""
    return Path("path/to/sample_internal_id_S1_L001_R1_001.fastq.gz")


@pytest.fixture(name="tmp_sample_sheet_path")
def tmp_samplesheet_path(tmp_demulitplexing_dir: Path) -> Path:
    """Return SampleSheet in temporary demuliplexing folder."""
    tmp_sample_sheet_path = Path(tmp_demulitplexing_dir, "SampleSheet.csv")
    with tmp_sample_sheet_path.open("w+") as fh:
        fh.write("content")
    return tmp_sample_sheet_path


@pytest.fixture(name="tmp_flow_cell_run_base_path")
def tmp_flow_cell_run_base_path(project_dir: Path, bcl2fastq_flow_cell_full_name: str) -> Path:
    """Flow cell run directory in temporary folder."""

    tmp_flow_cell_run_path: Path = Path(project_dir, "flow_cells")
    tmp_flow_cell_run_path.mkdir(exist_ok=True, parents=True)

    return tmp_flow_cell_run_path


@pytest.fixture(name="tmp_flow_cell_demux_base_path")
def tmp_flow_cell_demux_base_path(project_dir: Path, bcl2fastq_flow_cell_full_name: str) -> Path:
    """Flow cell demux directory in temporary folder."""

    tmp_flow_cell_demux_path: Path = Path(project_dir, "demultiplexed-runs")
    tmp_flow_cell_demux_path.mkdir(exist_ok=True, parents=True)

    return tmp_flow_cell_demux_path


@pytest.fixture(name="flow_cell_project_id")
def flow_cell_project_id() -> int:
    """Return flow cell run project id."""
    return 174578


@pytest.fixture(name="hiseq_x_copy_complete_file")
def hiseq_x_copy_complete_file(bcl2fastq_flow_cell: FlowCellDirectoryData) -> Path:
    """Return HiSeqX flow cell copy complete file."""
    return Path(bcl2fastq_flow_cell.path, DemultiplexingDirsAndFiles.HISEQ_X_COPY_COMPLETE)


@pytest.fixture(name="populated_flow_cell_store")
def populated_flow_cell_store(
    family_name: str,
    bcl2fastq_flow_cell_id: str,
    sample_id: str,
    store: Store,
    helpers: StoreHelpers,
) -> Store:
    """Populate a store with a NovaSeq flow cell."""

    populated_flow_cell_store: Store = store
    sample: Sample = helpers.add_sample(store=populated_flow_cell_store, internal_id=sample_id)
    family: Case = helpers.add_case(store=populated_flow_cell_store, internal_id=family_name)
    helpers.add_relationship(
        store=populated_flow_cell_store,
        sample=sample,
        case=family,
    )
    helpers.add_flow_cell(
        store=populated_flow_cell_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return populated_flow_cell_store


@pytest.fixture(name="active_flow_cell_store")
def active_flow_cell_store(
    family_name: str,
    bcl2fastq_flow_cell_id: str,
    sample_id: str,
    base_store: Store,
    helpers: StoreHelpers,
) -> Store:
    """Populate a store with a Novaseq flow cell, with active samples on it."""
    active_flow_cell_store: Store = base_store
    sample: Sample = helpers.add_sample(store=active_flow_cell_store, internal_id=sample_id)
    family: Case = helpers.add_case(
        store=active_flow_cell_store, internal_id=family_name, action="running"
    )
    helpers.add_relationship(
        store=active_flow_cell_store,
        sample=sample,
        case=family,
    )
    helpers.add_flow_cell(
        store=active_flow_cell_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return active_flow_cell_store


@pytest.fixture(name="sample_level_housekeeper_api")
def sample_level_housekeeper_api(
    bcl2fastq_flow_cell_id: str,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: list[Path],
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
def flow_cell_name_housekeeper_api(
    bcl2fastq_flow_cell_id: str,
    real_housekeeper_api: HousekeeperAPI,
    sample_id: str,
    tmp_fastq_paths: list[Path],
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
def populated_delete_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    populated_flow_cell_store: Store,
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    populated_delete_demux_context = cg_context
    populated_delete_demux_context.status_db_ = populated_flow_cell_store
    populated_delete_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    return populated_delete_demux_context


@pytest.fixture(name="populated_sample_lane_seq_demux_context")
def populated_sample_lane_seq_demux_context(
    cg_context: CGConfig,
    flow_cell_name_housekeeper_api: HousekeeperAPI,
    store_with_sequencing_metrics: Store,
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    populated_wipe_demux_context = cg_context
    populated_wipe_demux_context.status_db_ = store_with_sequencing_metrics
    populated_wipe_demux_context.housekeeper_api_ = flow_cell_name_housekeeper_api
    return populated_wipe_demux_context


@pytest.fixture(name="active_delete_demux_context")
def active_delete_demux_context(
    cg_context: CGConfig, active_flow_cell_store: Store, tmp_flow_cell_run_base_path: Path
) -> CGConfig:
    """Return a populated context to remove flow cells from using the DeleteDemuxAPI."""
    active_delete_demux_context = cg_context
    active_delete_demux_context.status_db_ = active_flow_cell_store
    active_delete_demux_context.demultiplex_api.flow_cells_dir = tmp_flow_cell_run_base_path
    active_delete_demux_context.demultiplex_api.demultiplexed_runs_dir = tmp_flow_cell_run_base_path
    return active_delete_demux_context


@pytest.fixture(name="populated_delete_demultiplex_api")
def populated_delete_demultiplex_api(
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
def populated_sample_lane_sequencing_metrics_demultiplex_api(
    populated_sample_lane_seq_demux_context: CGConfig, bcl2fastq_flow_cell_id
) -> DeleteDemuxAPI:
    """Return an initialized populated DeleteDemuxAPI."""
    return DeleteDemuxAPI(
        config=populated_sample_lane_seq_demux_context,
        dry_run=False,
        flow_cell_name=bcl2fastq_flow_cell_id,
    )


@pytest.fixture(name="active_delete_demultiplex_api")
def active_delete_demultiplex_api(
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
def delete_demultiplex_api(
    cg_context: CGConfig,
    bcl2fastq_flow_cell_id: str,
    tmp_flow_cell_run_base_path: Path,
) -> DeleteDemuxAPI:
    """Return an initialized DeleteDemuxAPI."""
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


@pytest.fixture(scope="session")
def flow_cell_name_demultiplexed_with_bcl_convert() -> str:
    return "HY7FFDRX2"


@pytest.fixture(scope="session")
def flow_cell_directory_name_demultiplexed_with_bcl_convert(
    flow_cell_name_demultiplexed_with_bcl_convert: str,
):
    return f"230504_A00689_0804_B{flow_cell_name_demultiplexed_with_bcl_convert}"


@pytest.fixture(scope="session")
def flow_cell_directory_name_demultiplexed_with_bcl_convert_flat(
    flow_cell_name_demultiplexed_with_bcl_convert: str,
):
    """Return the name of a flow cell directory that has been demultiplexed with Bcl Convert using a flat output directory structure."""
    return f"230505_A00689_0804_B{flow_cell_name_demultiplexed_with_bcl_convert}"


@pytest.fixture(scope="session")
def flow_cell_directory_name_demultiplexed_with_bcl_convert_on_sequencer(
    flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer: str,
):
    """Return the name of a flow cell directory that has been demultiplexed with Bcl Convert on the NovaseqX sequencer."""
    return f"20230508_LH00188_0003_A{flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer}"


@pytest.fixture(scope="session")
def flow_cell_name_demultiplexed_with_bcl_convert_on_sequencer() -> str:
    """Return the name of a flow cell directory that has been demultiplexed with Bcl Convert on the NovaseqX sequencer."""
    return "22522YLT3"


@pytest.fixture(name="demultiplexing_init_files")
def tmp_demultiplexing_init_files(
    bcl2fastq_flow_cell_id: str, populated_delete_demultiplex_api: DeleteDemuxAPI
) -> list[Path]:
    """Return a list of demultiplexing init files present in the run directory."""
    run_path: Path = populated_delete_demultiplex_api.run_path
    slurm_job_id_file_path: Path = Path(run_path, "slurm_job_ids.yaml")
    demux_script_file_path: Path = Path(run_path, "demux-novaseq.sh")
    error_log_path: Path = Path(run_path, f"{bcl2fastq_flow_cell_id}_demultiplex.stderr")
    log_path: Path = Path(run_path, f"{bcl2fastq_flow_cell_id}_demultiplex.stdout")

    demultiplexing_init_files: list[Path] = [
        slurm_job_id_file_path,
        demux_script_file_path,
        error_log_path,
        log_path,
    ]

    for file in demultiplexing_init_files:
        file.touch()
    return demultiplexing_init_files


@pytest.fixture(scope="session")
def bcl2fastq_folder_structure(tmp_path_factory, cg_dir: Path) -> Path:
    """Return a folder structure that resembles a bcl2fastq run folder."""
    base_dir: Path = tmp_path_factory.mktemp("".join((str(cg_dir), "bcl2fastq")))
    folders: list[str] = ["l1t21", "l1t11", "l2t11", "l2t21"]

    for folder in folders:
        new_dir: Path = Path(base_dir, folder)
        new_dir.mkdir()

    return base_dir


@pytest.fixture(scope="function")
def not_bcl2fastq_folder_structure(tmp_path_factory, cg_dir: Path) -> Path:
    """Return a folder structure that does not resemble a bcl2fastq run folder."""
    base_dir: Path = tmp_path_factory.mktemp("".join((str(cg_dir), "not_bcl2fastq")))
    folders: list[str] = ["just", "some", "folders"]

    for folder in folders:
        new_dir: Path = Path(base_dir, folder)
        new_dir.mkdir()

    return base_dir


@pytest.fixture(scope="session")
def base_call_file() -> Path:
    return Path("Data", "Intensities", "BaseCalls", "L001", "C1.1", "L001_1.cbcl")


@pytest.fixture(scope="session")
def inter_op_file() -> Path:
    return Path(DemultiplexingDirsAndFiles.INTER_OP, "AlignmentMetricsOut.bin")


@pytest.fixture(scope="session")
def thumbnail_file() -> Path:
    return Path("Thumbnail_Images", "L001", "C1.1", "s_1_1105_green.png")


@pytest.fixture
def lsyncd_source_directory(
    tmp_path_factory,
    novaseq_x_manifest_file: Path,
    base_call_file: Path,
    inter_op_file: Path,
    thumbnail_file: Path,
) -> Path:
    """Return a temporary directory with a manifest file and three dummy files."""
    source_directory = Path(tmp_path_factory.mktemp("source"))
    shutil.copy(novaseq_x_manifest_file, source_directory)
    for file in [base_call_file, inter_op_file, thumbnail_file]:
        full_path = Path(source_directory, file)
        full_path.parent.mkdir(parents=True)
        full_path.touch()
    return source_directory


@pytest.fixture
def lsyncd_target_directory(lsyncd_source_directory: Path, tmp_path_factory) -> Path:
    """Return a copy of the temporary source directory."""
    temp_target_directory = Path(tmp_path_factory.mktemp("tmp_target"))
    target_directory = Path(lsyncd_source_directory.parent, Path(temp_target_directory, "target"))
    shutil.copytree(lsyncd_source_directory, target_directory)
    return target_directory


@pytest.fixture
def demux_post_processing_api(
    demultiplex_context: CGConfig, tmp_demultiplexed_runs_directory: Path
) -> DemuxPostProcessingAPI:
    api = DemuxPostProcessingAPI(demultiplex_context)
    api.demultiplexed_runs_dir = tmp_demultiplexed_runs_directory
    return api


@pytest.fixture
def bcl2fastq_flow_cell_dir_name(demux_post_processing_api) -> str:
    """Return a flow cell name that has been demultiplexed with bcl2fastq."""
    flow_cell_dir_name = "170407_ST-E00198_0209_BHHKVCALXX"
    flow_cell_path = Path(demux_post_processing_api.demultiplexed_runs_dir, flow_cell_dir_name)

    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_path,
        flow_cell_name="HHKVCALXX",
        hk_api=demux_post_processing_api.hk_api,
    )
    return flow_cell_dir_name


@pytest.fixture
def bcl2fastq_sample_id_with_non_pooled_undetermined_reads() -> str:
    return "SVE2528A1"


@pytest.fixture
def bcl2fastq_non_pooled_sample_read_count() -> int:
    """Based on the data in 170407_ST-E00198_0209_BHHKVCALXX, the sum of all reads - mapped and undetermined."""
    return 8000000


@pytest.fixture
def bclconvert_flow_cell_dir_name(demux_post_processing_api) -> str:
    """Return a flow cell name that has been demultiplexed with bclconvert."""
    flow_cell_dir_name = "230504_A00689_0804_BHY7FFDRX2"
    flow_cell_path = Path(demux_post_processing_api.demultiplexed_runs_dir, flow_cell_dir_name)

    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_path,
        flow_cell_name="HY7FFDRX2",
        hk_api=demux_post_processing_api.hk_api,
    )
    return flow_cell_dir_name


@pytest.fixture
def bcl_convert_sample_id_with_non_pooled_undetermined_reads() -> str:
    return "ACC11927A2"


@pytest.fixture
def bcl_convert_non_pooled_sample_read_count() -> int:
    """Based on the data in 230504_A00689_0804_BHY7FFDRX2, the sum of all reads - mapped and undetermined."""
    return 4000000


def get_all_files_in_directory_tree(directory: Path) -> list[Path]:
    """Get the relative paths of all files in a directory and its subdirectories."""
    files_in_directory: list[Path] = []
    for subdir, _, files in os.walk(directory):
        subdir = Path(subdir).relative_to(directory)
        files_in_directory.extend([Path(subdir, file) for file in files])
    return files_in_directory
