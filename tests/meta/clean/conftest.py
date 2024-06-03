"""Tests for the CleanFlowCellsAPI."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.subject import Sex
from cg.meta.clean.clean_flow_cells import CleanFlowCellAPI
from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.models import Flowcell
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def flow_cell_clean_api_can_be_removed(
    tmp_flow_cell_to_clean_path: Path,
    store_with_flow_cell_to_clean: Store,
    housekeeper_api_with_flow_cell_to_clean: HousekeeperAPI,
    tmp_sample_sheet_clean_flow_cell_path: Path,
) -> CleanFlowCellAPI:
    """Return a CleanFlowCellAPI with a flow cell that can be removed."""
    clean_flow_cell_api = CleanFlowCellAPI(
        flow_cell_path=tmp_flow_cell_to_clean_path,
        status_db=store_with_flow_cell_to_clean,
        housekeeper_api=housekeeper_api_with_flow_cell_to_clean,
        dry_run=False,
    )
    clean_flow_cell_api.flow_cell._sample_sheet_path_hk = tmp_sample_sheet_clean_flow_cell_path
    return clean_flow_cell_api


@pytest.fixture(scope="function")
def flow_cell_clean_api_can_not_be_removed(
    tmp_flow_cell_not_to_clean_path: Path,
    store_with_flow_cell_not_to_clean: Store,
    real_housekeeper_api: HousekeeperAPI,
) -> CleanFlowCellAPI:
    """Return a CleanFlowCellAPI with a flow cell that can not be removed."""
    return CleanFlowCellAPI(
        flow_cell_path=tmp_flow_cell_not_to_clean_path,
        status_db=store_with_flow_cell_not_to_clean,
        housekeeper_api=real_housekeeper_api,
        dry_run=False,
    )


@pytest.fixture(scope="function")
def tmp_flow_cell_to_clean_path(tmp_flow_cell_directory_bcl_convert: Path):
    """Returns the path to a flow cell fulfilling all cleaning criteria."""
    return tmp_flow_cell_directory_bcl_convert


@pytest.fixture(scope="function")
def tmp_flow_cell_to_clean(tmp_flow_cell_to_clean_path: Path) -> IlluminaRunDirectoryData:
    """Returns a flow cell directory object for a flow cell that fulfills all cleaning criteria."""
    return IlluminaRunDirectoryData(tmp_flow_cell_to_clean_path)


@pytest.fixture(scope="function")
def tmp_flow_cell_not_to_clean_path(tmp_novaseq_6000_pre_1_5_kits_flow_cell_path: Path):
    """Return the path to a flow cell not fulfilling all cleaning criteria."""
    return tmp_novaseq_6000_pre_1_5_kits_flow_cell_path


@pytest.fixture(scope="function")
def tmp_flow_cell_not_to_clean(tmp_flow_cell_not_to_clean_path: Path) -> IlluminaRunDirectoryData:
    """Returns a flow cell directory object for a flow cell that does not fulfill all cleaning criteria."""
    return IlluminaRunDirectoryData(tmp_flow_cell_not_to_clean_path)


@pytest.fixture(scope="session")
def tmp_sample_sheet_clean_flow_cell_path(tmp_path_factory) -> Path:
    sample_sheet_path = tmp_path_factory.mktemp("SampleSheet.csv")
    return sample_sheet_path


@pytest.fixture
def store_with_flow_cell_to_clean(
    store: Store,
    sample_id: str,
    tmp_flow_cell_to_clean: IlluminaRunDirectoryData,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with multiple samples with sample lane sequencing metrics."""
    sample_sequencing_metrics_details: list[tuple] = [
        (sample_id, tmp_flow_cell_to_clean.id, 1, 50_000_0000, 90.5, 32),
        (sample_id, tmp_flow_cell_to_clean.id, 2, 50_000_0000, 90.4, 31),
    ]
    flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=tmp_flow_cell_to_clean.id,
        store=store,
        has_backup=True,
    )
    helpers.add_sample(
        store=store, customer_id="cust500", internal_id=sample_id, name=sample_id, sex=Sex.MALE
    )
    helpers.add_multiple_sample_lane_sequencing_metrics_entries(
        metrics_data=sample_sequencing_metrics_details, store=store
    )
    store.session.add(flow_cell)
    store.session.commit()
    return store


@pytest.fixture
def store_with_flow_cell_not_to_clean(
    store: Store,
    sample_id: str,
    tmp_flow_cell_not_to_clean: IlluminaRunDirectoryData,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with multiple samples with sample lane sequencing metrics."""
    sample_sequencing_metrics_details: list[str | int | float] = [
        (sample_id, tmp_flow_cell_not_to_clean.id, 1, 50_000_0000, 90.5, 32),
        (sample_id, tmp_flow_cell_not_to_clean.id, 2, 50_000_0000, 90.4, 31),
    ]
    flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=tmp_flow_cell_not_to_clean.id,
        store=store,
        has_backup=True,
    )
    helpers.add_sample(
        store=store, customer_id="cust500", internal_id=sample_id, name=sample_id, sex=Sex.MALE
    )
    helpers.add_multiple_sample_lane_sequencing_metrics_entries(
        metrics_data=sample_sequencing_metrics_details, store=store
    )
    store.session.add(flow_cell)
    store.session.commit()
    return store


@pytest.fixture(scope="function")
def housekeeper_api_with_flow_cell_to_clean(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_flow_cell_to_clean_bundle: dict,
    hk_sample_bundle_for_flow_cell_to_clean: dict,
) -> HousekeeperAPI:
    """
    Return a housekeeper api that contains a flow cell bundle with sample sheet,
    a sample bundle with a fastq and a SPRING file that are tagged with the flow cell.
    """
    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=hk_flow_cell_to_clean_bundle)
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_sample_bundle_for_flow_cell_to_clean
    )
    return real_housekeeper_api


@pytest.fixture(scope="function")
def housekeeper_api_with_flow_cell_not_to_clean(
    real_housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    hk_sample_bundle_for_flow_cell_not_to_clean: dict,
) -> HousekeeperAPI:
    """
    Return a housekeeper api that contains a flow cell bundle with sample sheet,
    a sample bundle with a fastq and a SPRING file that are tagged with the flow cell.
    """
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api, bundle_data=hk_sample_bundle_for_flow_cell_not_to_clean
    )
    return real_housekeeper_api


@pytest.fixture(scope="function")
def hk_flow_cell_to_clean_bundle(
    tmp_flow_cell_to_clean: IlluminaRunDirectoryData,
    timestamp_yesterday: datetime,
    tmp_sample_sheet_clean_flow_cell_path: Path,
) -> dict:
    """Housekeeper bundle information for a flow cell that can be cleaned."""
    return {
        "name": tmp_flow_cell_to_clean.id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": str(tmp_sample_sheet_clean_flow_cell_path),
                "archive": False,
                "tags": ["samplesheet", tmp_flow_cell_to_clean.id],
            }
        ],
    }


@pytest.fixture(scope="function")
def hk_sample_bundle_for_flow_cell_to_clean(
    sample_id: str,
    timestamp_yesterday: datetime,
    spring_file: Path,
    fastq_file: Path,
    spring_meta_data_file: Path,
    tmp_flow_cell_to_clean: IlluminaRunDirectoryData,
) -> dict:
    return {
        "name": sample_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": spring_file.as_posix(),
                "archive": False,
                "tags": [SequencingFileTag.SPRING, sample_id, tmp_flow_cell_to_clean.id],
            },
            {
                "path": fastq_file.as_posix(),
                "archive": False,
                "tags": [SequencingFileTag.FASTQ, sample_id, tmp_flow_cell_to_clean.id],
            },
            {
                "path": spring_meta_data_file.as_posix(),
                "archive": False,
                "tags": [SequencingFileTag.SPRING_METADATA, sample_id, tmp_flow_cell_to_clean.id],
            },
        ],
    }


@pytest.fixture(scope="function")
def hk_sample_bundle_for_flow_cell_not_to_clean(
    sample_id: str,
    timestamp_yesterday: datetime,
) -> dict:
    return {
        "name": sample_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [],
    }


@pytest.fixture
def clean_retrieved_spring_files_api(
    real_housekeeper_api: HousekeeperAPI, tmp_path
) -> CleanRetrievedSpringFilesAPI:
    """Returns a CleanRetrievedSpringFilesAPI."""
    real_housekeeper_api.root_dir = tmp_path
    return CleanRetrievedSpringFilesAPI(housekeeper_api=real_housekeeper_api, dry_run=False)


@pytest.fixture
def path_to_old_retrieved_spring_file() -> str:
    return Path("path", "to", "old_retrieved_spring_file").as_posix()


@pytest.fixture
def path_to_newly_retrieved_spring_file() -> str:
    return Path("path", "to", "newly_retrieved_spring_file").as_posix()


@pytest.fixture
def path_to_archived_but_not_retrieved_spring_file() -> str:
    return Path("path", "to", "archived_spring_file").as_posix()


@pytest.fixture
def path_to_fastq_file() -> str:
    return Path("path", "to", "fastq_file").as_posix()


@pytest.fixture
def paths_for_populated_clean_retrieved_spring_files_api(
    path_to_old_retrieved_spring_file: str,
    path_to_newly_retrieved_spring_file: str,
    path_to_archived_but_not_retrieved_spring_file: str,
    path_to_fastq_file: str,
) -> list[str]:
    return [
        path_to_old_retrieved_spring_file,
        path_to_newly_retrieved_spring_file,
        path_to_archived_but_not_retrieved_spring_file,
        path_to_fastq_file,
    ]


@pytest.fixture
def retrieved_test_bundle_name() -> str:
    return "retrieved_test_bundle"


@pytest.fixture
def path_to_old_spring_file_in_housekeeper(
    retrieved_test_bundle_name: str, path_to_old_retrieved_spring_file
) -> str:
    return Path(
        retrieved_test_bundle_name,
        str(datetime.today().date()),
        Path(path_to_old_retrieved_spring_file).name,
    ).as_posix()


@pytest.fixture
def populated_clean_retrieved_spring_files_api(
    clean_retrieved_spring_files_api: CleanRetrievedSpringFilesAPI,
    paths_for_populated_clean_retrieved_spring_files_api: list[str],
    retrieved_test_bundle_name: str,
    archival_job_id_miria: int,
    retrieval_job_id_miria: int,
    timestamp: datetime,
    timestamp_yesterday: datetime,
    old_timestamp: datetime,
    tmp_path,
) -> CleanRetrievedSpringFilesAPI:
    """
    Returns a populated CleanRetrievedSpringFilesAPI, containing a bundle with one version and the following files:
        - an archived Spring file which has not been retrieved
        - an archived Spring file which was retrieved 1 day ago
        - an archived Spring file which was retrieved in the year 1900
        - a Fastq file
    """
    clean_retrieved_spring_files_api.housekeeper_api.add_bundle_and_version_if_non_existent(
        bundle_name=retrieved_test_bundle_name
    )
    clean_retrieved_spring_files_api.housekeeper_api.commit()
    for path in paths_for_populated_clean_retrieved_spring_files_api:
        tags: list[str] = (
            [SequencingFileTag.SPRING]
            if SequencingFileTag.SPRING in path
            else [SequencingFileTag.FASTQ]
        )
        Path(tmp_path, path).parent.mkdir(parents=True, exist_ok=True)
        file_to_add = Path(tmp_path, path)
        file_to_add.touch()
        clean_retrieved_spring_files_api.housekeeper_api.add_and_include_file_to_latest_version(
            file=file_to_add, bundle_name=retrieved_test_bundle_name, tags=tags
        )
    for file in clean_retrieved_spring_files_api.housekeeper_api.get_files(
        bundle=retrieved_test_bundle_name
    ):
        Path(file.full_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file.full_path).touch()
        if "spring" in file.path:
            clean_retrieved_spring_files_api.housekeeper_api.add_archives(
                files=[file], archive_task_id=archival_job_id_miria
            )
            file.archive.archived_at = timestamp
            if "retrieved" in file.path:
                file.archive.retrieval_task_id = retrieval_job_id_miria
                file.archive.retrieved_at = (
                    old_timestamp if "old" in file.path else timestamp_yesterday
                )
            clean_retrieved_spring_files_api.housekeeper_api.add_commit(file.archive)

    clean_retrieved_spring_files_api.housekeeper_api.commit()
    return clean_retrieved_spring_files_api
