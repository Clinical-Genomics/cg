from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import File
from pytest_mock import MockerFixture
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import AnalysisNotReadyError
from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import BamFetcher
from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import Path as bam_path
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.fixture
def status_db() -> Store:
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)
    return status_db


def test_ensure_files_are_ready_success(status_db: Store, mocker: MockerFixture):
    # GIVEN that the samples have BAM files in Housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    file_query = create_autospec(Query)
    file_query.all = Mock(
        return_value=[
            create_autospec(File, full_path="non/existing/file"),
        ]
    )
    housekeeper_api.files = Mock(return_value=file_query)

    # GIVEN that the files are on disk
    mocker.patch.object(bam_path, "is_file", return_value=True)

    # GIVEN a BamFetcher
    bam_fetcher = BamFetcher(status_db=status_db, housekeeper_api=housekeeper_api)

    # WHEN ensuring that all files are ready
    bam_fetcher.ensure_files_are_ready("case_id")

    # THEN no error is raised


def test_ensure_files_are_ready_failure(status_db: Store, mocker: MockerFixture):
    # GIVEN that the samples have BAM files in Housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    query = create_autospec(Query)
    query.all = Mock(
        return_value=[
            create_autospec(File, full_path="non/existing/file1"),
            create_autospec(File, full_path="non/existing/file2"),
        ]
    )
    housekeeper_api.files = Mock(return_value=query)

    # GIVEN that the files are not on disk
    mocker.patch.object(bam_path, "is_file", return_value=False)

    # GIVEN a BamFetcher
    bam_fetcher = BamFetcher(status_db=status_db, housekeeper_api=housekeeper_api)

    # WHEN ensuring that all files are ready
    # THEN an error is raised
    with pytest.raises(AnalysisNotReadyError):
        bam_fetcher.ensure_files_are_ready("case_id")


def test_ensure_files_are_ready_missing_sample_files(status_db: Store):
    # GIVEN that the samples have no BAM files in Housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    query = create_autospec(Query)
    query.all = Mock(return_value=[])
    housekeeper_api.files = Mock(return_value=query)

    # GIVEN a BamFetcher
    bam_fetcher = BamFetcher(status_db=status_db, housekeeper_api=housekeeper_api)

    # WHEN ensuring that all files are ready
    # THEN an error is raised
    with pytest.raises(AnalysisNotReadyError):
        bam_fetcher.ensure_files_are_ready("case_id")
