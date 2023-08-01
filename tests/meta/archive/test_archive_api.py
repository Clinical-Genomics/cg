from pathlib import Path

from cg.constants.archiving import ArchiveLocationsInUse

from typing import List
from unittest import mock

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import APIMethods
from cg.io.controller import APIRequest
from cg.meta.archive.archive import SpringArchiveAPI, PathAndSample

from cg.store.models import Sample


def test_get_files_by_archive_location(
    spring_archive_api: SpringArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    """Tests the fetching of sample/customer info from statusdb based on bundle_names
    and returning the samples with the given Archive location."""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # Given non-archived spring files


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


def test_sort_spring_files_on_archive_location(
    spring_archive_api: SpringArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN fetching all non-archived spring files
    non_archived_spring_files: List[PathAndSample] = [
        PathAndSample(path=path, sample_internal_id=sample)
        for sample, path in populated_housekeeper_api.get_non_archived_spring_path_and_bundle_name()
    ]
    # WHEN extracting the files based on data archive
    sorted_spring_files: List[PathAndSample] = spring_archive_api.get_files_by_archive_location(
        non_archived_spring_files, archive_location=ArchiveLocationsInUse.KAROLINSKA_BUCKET
    )

    # THEN there should be spring files
    assert sorted_spring_files
    for file_and_sample in sorted_spring_files:
        sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(
            file_and_sample.sample_internal_id
        )
        # THEN each file should be correctly sorted on its archive location
        assert sample.customer.data_archive_location == ArchiveLocationsInUse.KAROLINSKA_BUCKET


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


def test_archive_all_non_archived_spring_files(
    spring_archive_api: SpringArchiveAPI,
    caplog,
    transfer_data_archive,
    ok_ddn_response,
    spring_file: Path,
):
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

    # THEN the log should report that the PDC sample was skipped
    assert "No support for archiving using the location: PDC" in caplog.text


def test_retrieve_sample():
    assert False
