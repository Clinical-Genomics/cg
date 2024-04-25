import os
import shutil
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers

FlowCellInfo = namedtuple("FlowCellInfo", "directory name sample_internal_ids")


@pytest.fixture(name="tmp_demulitplexing_dir")
def tmp_illumina_novaseq_demulitplexing_dir(
    illumina_demultiplexed_runs_directory: Path, novaseq_6000_pre_1_5_kits_flow_cell_full_name: str
) -> Path:
    """Return a tmp directory in demultiplexed-runs."""
    tmp_demulitplexing_dir: Path = Path(
        illumina_demultiplexed_runs_directory, novaseq_6000_pre_1_5_kits_flow_cell_full_name
    )
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


@pytest.fixture
def tmp_sample_sheet_path(tmp_demulitplexing_dir: Path) -> Path:
    """Return SampleSheet in temporary demuliplexing folder."""
    tmp_sample_sheet_path = Path(tmp_demulitplexing_dir, "SampleSheet.csv")
    with tmp_sample_sheet_path.open("w+") as fh:
        fh.write("content")
    return tmp_sample_sheet_path


@pytest.fixture(name="populated_flow_cell_store")
def populated_flow_cell_store(
    family_name: str,
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
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
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return populated_flow_cell_store


@pytest.fixture
def active_flow_cell_store(
    family_name: str,
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
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
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
        sequencer_type="novaseq",
        samples=[sample],
    )
    return active_flow_cell_store


@pytest.fixture(name="sample_level_housekeeper_api")
def sample_level_housekeeper_api(
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
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
            {
                "path": path.as_posix(),
                "tags": ["fastq", novaseq_6000_pre_1_5_kits_flow_cell_id],
                "archive": False,
            }
            for path in tmp_fastq_paths
        ],
    }
    helpers.ensure_hk_bundle(store=sample_level_housekeeper_api, bundle_data=bundle_data)
    return sample_level_housekeeper_api


@pytest.fixture(name="flow_cell_name_housekeeper_api")
def flow_cell_name_housekeeper_api(
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
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
            {
                "path": path.as_posix(),
                "tags": ["fastq", novaseq_6000_pre_1_5_kits_flow_cell_id],
                "archive": False,
            }
            for path in tmp_fastq_paths
        ],
    }
    flow_cell_bundle_data = {
        "name": novaseq_6000_pre_1_5_kits_flow_cell_id,
        "created": datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": tmp_sample_sheet_path.as_posix(),
                "tags": ["samplesheet", novaseq_6000_pre_1_5_kits_flow_cell_id],
                "archive": False,
            }
        ],
    }

    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=bundle_data)
    helpers.ensure_hk_bundle(store=flow_cell_housekeeper_api, bundle_data=flow_cell_bundle_data)
    return flow_cell_housekeeper_api


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


def get_all_files_in_directory_tree(directory: Path) -> list[Path]:
    """Get the relative paths of all files in a directory and its subdirectories."""
    files_in_directory: list[Path] = []
    for subdir, _, files in os.walk(directory):
        subdir = Path(subdir).relative_to(directory)
        files_in_directory.extend([Path(subdir, file) for file in files])
    return files_in_directory
