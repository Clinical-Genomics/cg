from typing import List
from unittest import mock

from cg.constants.archiving import ArchiveLocations
from cg.meta.archive.archive import (
    FileAndSample,
    SpringArchiveAPI,
    filter_files_on_archive_location,
)
from cg.meta.archive.ddn_dataflow import MiriaFile
from cg.meta.archive.models import FileTransferData
from cg.store.models import Sample
from housekeeper.store.models import File


def test_get_files_by_archive_location(
    spring_archive_api: SpringArchiveAPI, sample_id, father_sample_id
):
    """Tests filtering out files and samples with the correct Archive location from a list."""
    files_and_samples: List[FileAndSample] = [
        FileAndSample(
            file=spring_archive_api.housekeeper_api.get_files(bundle=sample).first(),
            sample=spring_archive_api.status_db.get_sample_by_internal_id(sample),
        )
        for sample in [sample_id, father_sample_id]
    ]
    # WHEN fetching the files by archive location
    selected_files: List[FileAndSample] = filter_files_on_archive_location(
        files_and_samples, ArchiveLocations.KAROLINSKA_BUCKET
    )

    # THEN every file returned should have that archive location
    assert selected_files
    for selected_file in selected_files:
        assert selected_file.sample.archive_location == ArchiveLocations.KAROLINSKA_BUCKET


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


def test_get_sample_exists(sample_id: str, spring_archive_api: SpringArchiveAPI):
    """Tests fetching a sample when the sample exists."""
    # GIVEN a sample that exists in the database
    file: File = spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first()

    # WHEN getting the sample
    sample: Sample = spring_archive_api.get_sample(file)

    # THEN the correct sample should be returned
    assert sample.internal_id == sample_id


def test_get_sample_not_exists(
    caplog,
    spring_archive_api: SpringArchiveAPI,
    sample_id,
):
    """Tests fetching a sample when the sample does not exist."""
    # GIVEN a sample that does not exist in the database
    file: File = spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first()
    sample_id: str = "non-existent-sample"
    file.version.bundle.name = sample_id

    # WHEN getting the sample
    sample: Sample = spring_archive_api.get_sample(file)

    # THEN the no sample should be returned
    # THEN both sample_id and file path should be logged
    assert not sample
    assert sample_id in caplog.text
    assert file.path in caplog.text


def test_convert_into_transfer_data(sample_id: str, spring_archive_api: SpringArchiveAPI):
    """Tests instantiating the correct dataclass for a sample."""
    # GIVEN file and Sample
    file_and_sample = FileAndSample(
        file=spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first(),
        sample=spring_archive_api.status_db.get_sample_by_internal_id(sample_id),
    )
    # WHEN using it to instantiate the correct class
    transferdata: List[FileTransferData] = spring_archive_api.convert_files_into_transfer_data(
        files_and_samples=[file_and_sample],
        archive_location=ArchiveLocations.KAROLINSKA_BUCKET,
    )

    # THEN the returned object should be of the correct type
    assert isinstance(transferdata[0], MiriaFile)


def test_call_corresponding_archiving_method(
    spring_archive_api: SpringArchiveAPI, miria_file_archive: MiriaFile
):
    """Tests so that the correct archiving function is used when providing a Karolinska customer."""
    # GIVEN a file to be transferred
    # GIVEN a spring_archive_api with a mocked archive function
    with mock.patch.object(
        spring_archive_api.ddn_client,
        "archive_folders",
        return_value=123,
    ) as mock_request_submitter:
        # WHEN calling the corresponding archive method
        spring_archive_api.call_corresponding_archiving_method(
            files=[miria_file_archive], archive_location=ArchiveLocations.KAROLINSKA_BUCKET
        )

    # THEN the correct archive function should have been called once
    mock_request_submitter.assert_called_once_with(sources_and_destinations=[miria_file_archive])
