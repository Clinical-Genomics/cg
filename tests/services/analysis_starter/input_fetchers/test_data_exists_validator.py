from unittest.mock import ANY, Mock, create_autospec

import pytest
from housekeeper.store.models import File
from pytest_mock import MockerFixture
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.exc import AnalysisNotReadyError
from cg.services.analysis_starter.analysis_input_validator.implementations.data_exists_validator import (
    DataExistsValidator,
)
from cg.services.analysis_starter.analysis_input_validator.implementations.data_exists_validator import (
    Path as file_path,
)
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def status_db() -> Store:
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample, internal_id="sample_id")
    case: Case = create_autospec(Case, data_analysis=Workflow.NALLO, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)
    return status_db


def test_ensure_files_are_ready_bam_success(mocker: MockerFixture):
    # GIVEN a store that returns a BAM case
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample, internal_id="sample_id")
    case: Case = create_autospec(Case, data_analysis=Workflow.NALLO, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN that the samples have BAM files in Housekeeper
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    file_query: Query = create_autospec(Query)
    file_query.all = Mock(
        return_value=[
            create_autospec(File, full_path="non/existing/file"),
        ]
    )
    housekeeper_api.as_type.files = Mock(return_value=file_query)

    # GIVEN that the files are on disk
    mocker.patch.object(file_path, "is_file", return_value=True)

    # GIVEN a DataExistsValidator
    data_exists_validator = DataExistsValidator(
        status_db=status_db, housekeeper_api=housekeeper_api.as_type
    )

    # WHEN ensuring that all files are ready
    data_exists_validator.ensure_files_are_ready("case_id")

    # THEN no error is raised

    # THEN files were fetched using the correct tags
    housekeeper_api.as_mock.files.assert_called_with(bundle=ANY, tags={"bam"})


def test_ensure_files_are_ready_fastq_success(mocker: MockerFixture):
    # GIVEN a store that returns a Fastq case
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(Sample, internal_id="sample_id")
    case: Case = create_autospec(Case, data_analysis=Workflow.TRANA_16S, samples=[sample])
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN that the samples have Fastq files in Housekeeper
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    file_query: Query = create_autospec(Query)
    file_query.all = Mock(
        return_value=[
            create_autospec(File, full_path="non/existing/file"),
        ]
    )
    housekeeper_api.as_type.files = Mock(return_value=file_query)

    # GIVEN that the files are on disk
    mocker.patch.object(file_path, "is_file", return_value=True)

    # GIVEN a DataExistsValidator
    data_exists_validator = DataExistsValidator(
        status_db=status_db, housekeeper_api=housekeeper_api.as_type
    )

    # WHEN ensuring that all files are ready
    data_exists_validator.ensure_files_are_ready("case_id")

    # THEN no error is raised

    # THEN files were fetched using the correct tags
    housekeeper_api.as_mock.files.assert_called_with(bundle=ANY, tags={"fastq"})


def test_ensure_files_are_ready_raw_data_not_on_disk(status_db: Store, mocker: MockerFixture):
    # GIVEN that the samples have BAM files in Housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    file_query: Query = create_autospec(Query)
    file_query.all = Mock(
        return_value=[
            create_autospec(File, full_path="non/existing/file1"),
            create_autospec(File, full_path="non/existing/file2"),
        ]
    )
    housekeeper_api.files = Mock(return_value=file_query)

    # GIVEN that the files are not on disk
    mocker.patch.object(file_path, "is_file", return_value=False)

    # GIVEN a DataExistsValidator
    data_exists_validator = DataExistsValidator(
        status_db=status_db, housekeeper_api=housekeeper_api
    )

    # WHEN ensuring that all files are ready
    # THEN an error is raised
    with pytest.raises(AnalysisNotReadyError):
        data_exists_validator.ensure_files_are_ready("case_id")


def test_ensure_files_are_ready_missing_sample_files(status_db: Store):
    # GIVEN that the samples have no BAM files in Housekeeper
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    file_query: Query = create_autospec(Query)
    file_query.all = Mock(return_value=[])
    housekeeper_api.files = Mock(return_value=file_query)

    # GIVEN a DataExistsValidator
    data_exists_validator = DataExistsValidator(
        status_db=status_db, housekeeper_api=housekeeper_api
    )

    # WHEN ensuring that all files are ready
    # THEN an error is raised
    with pytest.raises(AnalysisNotReadyError):
        data_exists_validator.ensure_files_are_ready("case_id")
