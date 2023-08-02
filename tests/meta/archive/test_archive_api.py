from pathlib import Path

from housekeeper.store.models import File

from typing import List
from unittest import mock

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import ArchiveLocationsInUse
from cg.constants.constants import APIMethods
from cg.io.controller import APIRequest
from cg.meta.archive.archive import (
    SpringArchiveAPI,
    PathAndSample,
    FileAndSample,
    get_files_by_archive_location,
)
from cg.meta.archive.ddn_dataflow import DataFlowFileTransferData
from cg.meta.archive.models import FileTransferData

from cg.store.models import Sample


def test_get_files_by_archive_location(
    spring_archive_api: SpringArchiveAPI, sample_id, father_sample_id
):
    """Tests filtering out files and samples with the correct Archive location from a list."""
    # GIVEN two Samples and two corresponding files
    files_and_samples: List[FileAndSample] = []
    for sample in [sample_id, father_sample_id]:
        files_and_samples.append(
            FileAndSample(
                file=spring_archive_api.housekeeper_api.get_files(bundle=sample).first(),
                sample=spring_archive_api.status_db.get_sample_by_internal_id(sample),
            )
        )
    # WHEN fetching the files by archive location
    selected_files: List[FileAndSample] = get_files_by_archive_location(
        files_and_samples, ArchiveLocationsInUse.KAROLINSKA_BUCKET
    )

    # THEN every file returned should have that archive location
    assert selected_files
    for selected_file in selected_files:
        assert selected_file.sample.archive_location == ArchiveLocationsInUse.KAROLINSKA_BUCKET


def test_archive_samples(
    spring_archive_api: SpringArchiveAPI, populated_housekeeper_api: HousekeeperAPI, sample_id: str
):
    # GIVEN a list of sample ids whit housekeeper bundles and SPRING files
    sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(sample_id)
    # WHEN archiving these samples
    spring_archive_api.archive_samples(samples=[sample])
    # THEN tha archive objects should be added to housekeeper along with a task_id

    assert (
        populated_housekeeper_api.files(
            bundle=sample.internal_id, tags={SequencingFileTag.SPRING, sample.internal_id}
        )
        .first()
        .archive
    )


def test_add_samples_to_files(spring_archive_api: SpringArchiveAPI):
    """Tests matching Files to Samples when both files have a matching sample."""
    # GIVEN a list of SPRING Files to archive
    files_to_archive: List[
        File
    ] = spring_archive_api.housekeeper_api.get_all_non_archived_spring_files()

    # WHEN adding the Sample objects
    file_and_samples: List[FileAndSample] = spring_archive_api.add_samples_to_files(
        files_to_archive
    )

    # THEN each file should have a matching sample
    assert len(files_to_archive) == len(file_and_samples) > 0
    for file_and_sample in file_and_samples:
        # THEN the bundle name of each file should match the sample internal id
        assert file_and_sample.file.version.bundle.name == file_and_sample.sample.internal_id


def test_add_samples_to_files_missing_sample(spring_archive_api: SpringArchiveAPI):
    """Tests matching Files to Samples when one of the files does not match a Sample."""
    # GIVEN a list of SPRING Files to archive
    files_to_archive: List[
        File
    ] = spring_archive_api.housekeeper_api.get_all_non_archived_spring_files()
    # GIVEN one of the files does not match the
    files_to_archive[0].version.bundle.name = "does-not-exist"
    # WHEN adding the Sample objects
    file_and_samples: List[FileAndSample] = spring_archive_api.add_samples_to_files(
        files_to_archive
    )

    # THEN only one of the files should have a matching sample
    assert len(files_to_archive) != len(file_and_samples) > 0
    for file_and_sample in file_and_samples:
        # THEN the bundle name of each file should match the sample internal id
        assert file_and_sample.file.version.bundle.name == file_and_sample.sample.internal_id


def test_get_sample_exists(sample_id: str, spring_archive_api: SpringArchiveAPI, spring_file: Path):
    """Tests fetching a sample when the sample exists."""
    # GIVEN a sample that exists in the database
    file_info: PathAndSample = PathAndSample(spring_file, sample_id)

    # WHEN getting the sample
    sample: Sample = spring_archive_api.get_sample(file_info)

    # THEN the correct sample should be returned
    assert sample.internal_id == sample_id


def test_get_sample_not_exists(caplog, spring_archive_api: SpringArchiveAPI, spring_file: Path):
    """Tests fetching a sample when the sample does not exist."""
    # GIVEN a sample that does not exist in the database
    sample_id: str = "non-existent-sample"
    file_info: PathAndSample = PathAndSample(spring_file, sample_id)

    # WHEN getting the sample
    sample: Sample = spring_archive_api.get_sample(file_info)

    # THEN the no sample should be returned
    # THEN both sample_id and file path should be logged
    assert not sample
    assert sample_id in caplog.text
    assert spring_file.as_posix() in caplog.text


def test_convert_into_correct_model(sample_id: str, spring_archive_api: SpringArchiveAPI):
    """Tests instantiating the correct dataclass for a sample."""
    # GIVEN file and Sample
    file_and_sample = FileAndSample(
        file=spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first(),
        sample=spring_archive_api.status_db.get_sample_by_internal_id(sample_id),
    )
    # WHEN using it to instantiate the correct class
    transferdata: List[FileTransferData] = spring_archive_api.convert_into_correct_model(
        files_and_samples=[file_and_sample],
        archive_location=ArchiveLocationsInUse.KAROLINSKA_BUCKET,
    )

    # THEN the returned object should be of the correct type
    assert type(transferdata[0]) == DataFlowFileTransferData


def test_call_corresponding_archiving_function(
    spring_archive_api: SpringArchiveAPI, transfer_data_archive: DataFlowFileTransferData
):
    """Tests so that the correct archiving function is used when"""
    # GIVEN a file to be transferred
    # GIVEN a spring_archive_api with a mocked archive function
    with mock.patch.object(
        spring_archive_api.ddn_api,
        "archive_folders",
        return_value=123,
    ) as mock_request_submitter:
        # WHEN calling the corresponding archive method
        spring_archive_api.call_corresponding_archiving_function(
            files=[transfer_data_archive], archive_location=ArchiveLocationsInUse.KAROLINSKA_BUCKET
        )

    # THEN the correct archive function should have been called once
    mock_request_submitter.assert_called_once_with(sources_and_destinations=[transfer_data_archive])


def test_archive_all_non_archived_spring_files(
    spring_archive_api: SpringArchiveAPI,
    caplog,
    transfer_data_archive,
    ok_ddn_response,
):
    """Test archiving all non-archived SPRING files"""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN archiving all available samples

    with mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_ddn_response,
    ) as mock_request_submitter:
        spring_archive_api.archive_all_non_archived_spring_files()

    # THEN the DDN archiving function should have been called
    mock_request_submitter.assert_called_once_with(
        api_method=APIMethods.POST,
        url="some/api/files/archive",
        headers={
            "Content-Type": "application/json",
            "accept": "application/json",
            "Authorization": "Bearer test_auth_token",
        },
        json={
            "osType": "Unix/MacOS",
            "createFolder": False,
            "pathInfo": [
                {
                    "destination": "archive@repisitory:ADM1",
                    "source": "local@storage:/tests/fixtures/apps/demultiplexing/demultiplexed-runs/spring/dummy_run_001.spring",
                }
            ],
            "metadataList": [],
        },
    )
