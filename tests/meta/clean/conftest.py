"""Tests for the CleanFlowCellsAPI."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from housekeeper.store.models import Bundle, File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.subject import Sex
from cg.meta.clean.clean_flow_cells import CleanFlowCellAPI
from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, Sample
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
def tmp_flow_cell_to_clean_path(tmp_flow_cell_directory_bclconvert: Path):
    """Returns the path to a flow cell fulfilling all cleaning criteria."""
    return tmp_flow_cell_directory_bclconvert


@pytest.fixture(scope="function")
def tmp_flow_cell_to_clean(tmp_flow_cell_to_clean_path: Path) -> FlowCellDirectoryData:
    """Returns a flow cell directory object for a flow cell that fulfills all cleaning criteria."""
    return FlowCellDirectoryData(tmp_flow_cell_to_clean_path)


@pytest.fixture(scope="function")
def tmp_flow_cell_not_to_clean_path(tmp_flow_cell_directory_bcl2fastq: Path):
    """Return the path to a flow cell not fulfilling all cleaning criteria."""
    return tmp_flow_cell_directory_bcl2fastq


@pytest.fixture(scope="function")
def tmp_flow_cell_not_to_clean(tmp_flow_cell_not_to_clean_path: Path) -> FlowCellDirectoryData:
    """Returns a flow cell directory object for a flow cell that does not fulfill all cleaning criteria."""
    return FlowCellDirectoryData(tmp_flow_cell_not_to_clean_path)


@pytest.fixture(scope="session")
def tmp_sample_sheet_clean_flow_cell_path(tmp_path_factory) -> Path:
    sample_sheet_path = tmp_path_factory.mktemp("SampleSheet.csv")
    return sample_sheet_path


@pytest.fixture
def store_with_flow_cell_to_clean(
    store: Store,
    sample_id: str,
    tmp_flow_cell_to_clean: FlowCellDirectoryData,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with multiple samples with sample lane sequencing metrics."""
    sample_sequencing_metrics_details: list[str | int | float] = [
        (sample_id, tmp_flow_cell_to_clean.id, 1, 50_000_0000, 90.5, 32),
        (sample_id, tmp_flow_cell_to_clean.id, 2, 50_000_0000, 90.4, 31),
    ]
    flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=tmp_flow_cell_to_clean.id,
        store=store,
        has_backup=True,
    )
    sample: Sample = helpers.add_sample(
        store=store, customer_id="cust500", internal_id=sample_id, name=sample_id, sex=Sex.MALE
    )
    helpers.add_multiple_sample_lane_sequencing_metrics_entries(
        metrics_data=sample_sequencing_metrics_details, store=store
    )
    flow_cell.samples = [sample]
    store.session.add(flow_cell)
    store.session.commit()
    return store


@pytest.fixture
def store_with_flow_cell_not_to_clean(
    store: Store,
    sample_id: str,
    tmp_flow_cell_not_to_clean: FlowCellDirectoryData,
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
    sample: Sample = helpers.add_sample(
        store=store, customer_id="cust500", internal_id=sample_id, name=sample_id, sex=Sex.MALE
    )
    helpers.add_multiple_sample_lane_sequencing_metrics_entries(
        metrics_data=sample_sequencing_metrics_details, store=store
    )
    flow_cell.samples = [sample]
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
    tmp_flow_cell_to_clean: FlowCellDirectoryData,
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
    tmp_flow_cell_to_clean: FlowCellDirectoryData,
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
def clean_retrieved_spring_files_api_dry_run(
    real_housekeeper_api: HousekeeperAPI,
) -> CleanRetrievedSpringFilesAPI:
    """Returns a CleanRetrievedSpringFilesAPI."""
    return CleanRetrievedSpringFilesAPI(housekeeper_api=real_housekeeper_api, dry_run=True)


@pytest.fixture
def path_to_old_retrieved_spring_file() -> str:
    return Path("path", "to", "old", "retrieved", "spring", "file").as_posix()


@pytest.fixture
def path_to_old_retrieved_spring_file_in_housekeeper(path_to_old_retrieved_spring_file) -> str:
    return Path(path_to_old_retrieved_spring_file).absolute().as_posix()


@pytest.fixture
def path_to_newly_retrieved_spring_file() -> str:
    return Path("path", "to", "newly", "retrieved", "spring", "file").as_posix()


@pytest.fixture
def path_to_archived_but_not_retrieved_spring_file() -> str:
    return Path("path", "to", "archived", "spring", "file").as_posix()


@pytest.fixture
def path_to_fastq_file() -> str:
    return Path("path", "to", "fastq", "file").as_posix()


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
def archived_at_timestamp() -> datetime:
    return datetime.now() - timedelta(weeks=52)


@pytest.fixture
def retrieved_at_old_timestamp() -> datetime:
    return datetime.now() - timedelta(weeks=50)


@pytest.fixture
def retrieved_at_new_timestamp() -> datetime:
    return datetime.now() - timedelta(days=1)


@pytest.fixture
def populated_clean_retrieved_spring_files_api_dry_run(
    clean_retrieved_spring_files_api_dry_run: CleanRetrievedSpringFilesAPI,
    paths_for_populated_clean_retrieved_spring_files_api: list[str],
    retrieved_test_bundle_name: str,
    archival_job_id_miria: int,
    retrieval_job_id_miria: int,
    archived_at_timestamp: datetime,
    retrieved_at_old_timestamp: datetime,
    retrieved_at_new_timestamp: datetime,
) -> CleanRetrievedSpringFilesAPI:
    """
    Returns a populated CleanRetrievedSpringFilesAPI, containing a bundle with one version and the following files:
        - an archived Spring file which has not been retrieved
        - an archived Spring file which was retrieved 1 day ago
        - an archived Spring file which was retrieved 1 year ago
        - a Fastq file
    """
    clean_retrieved_spring_files_api_dry_run.housekeeper_api.add_bundle_and_version_if_non_existent(
        bundle_name=retrieved_test_bundle_name
    )
    bundle: Bundle = clean_retrieved_spring_files_api_dry_run.housekeeper_api.bundle(
        retrieved_test_bundle_name
    )
    version: Version = bundle.versions[0]
    for path in paths_for_populated_clean_retrieved_spring_files_api:
        tags: list[str] = (
            [SequencingFileTag.SPRING]
            if SequencingFileTag.SPRING in path
            else [SequencingFileTag.FASTQ]
        )
        file: File = clean_retrieved_spring_files_api_dry_run.housekeeper_api.add_file(
            path=path, version_obj=version, tags=tags
        )
        clean_retrieved_spring_files_api_dry_run.housekeeper_api.commit()
        if "spring" in path:
            clean_retrieved_spring_files_api_dry_run.housekeeper_api.add_archives(
                files=[file], archive_task_id=archival_job_id_miria
            )
            file.archive.archived_at = archived_at_timestamp
            if "retrieved" in path:
                file.archive.retrieval_task_id = retrieval_job_id_miria
                file.archive.retrieved_at = (
                    retrieved_at_old_timestamp if "old" in path else retrieved_at_new_timestamp
                )
            clean_retrieved_spring_files_api_dry_run.housekeeper_api.add_commit(file.archive)

    clean_retrieved_spring_files_api_dry_run.housekeeper_api.commit()
    return clean_retrieved_spring_files_api_dry_run
