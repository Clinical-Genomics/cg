"""Tests for the CleanFlowCellsAPI."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.clean.clean_retrieved_spring_files import CleanRetrievedSpringFilesAPI


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
