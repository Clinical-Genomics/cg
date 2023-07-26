from pathlib import Path
from typing import List, Dict
from unittest import mock

from housekeeper.store.models import File

import cg.meta.archive.ddn_dataflow
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import APIMethods
from cg.io.controller import APIRequest
from cg.meta.archive.archive import ArchiveAPI, PathAndSample, ARCHIVES_IN_USE
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferPayload
from cg.store.models import Sample


def test_archive_samples(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI, sample_id: str
):
    # GIVEN a list of sample ids whit housekeeper bundles and SPRING files
    sample: Sample = archive_api.status_db.get_sample_by_internal_id(sample_id)
    # WHEN archiving these samples
    archive_api.archive_samples(samples=[sample])
    # THEN tha archive objects should be added to housekeeper along with a task_id

    assert (
        populated_housekeeper_api.files(
            bundle=sample.internal_id, tags={SequencingFileTag.SPRING, sample.internal_id}
        )
        .first()
        .archive
    )


def test_sort_spring_files_on_archive_location(
    archive_api: ArchiveAPI, populated_housekeeper_api: HousekeeperAPI
):
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN fetching all non-archived spring files
    non_archived_spring_files: List[PathAndSample] = [
        PathAndSample(path=path, sample_internal_id=sample)
        for sample, path in populated_housekeeper_api.get_non_archived_spring_path_and_bundle_name()
    ]
    # WHEN sorting the returned files on the data archive locations of the customers
    sorted_spring_files: Dict[
        str, List[PathAndSample]
    ] = archive_api.sort_files_on_archive_location(non_archived_spring_files)

    # THEN there should be spring files
    assert sorted_spring_files
    for archive_location, files_and_samples in sorted_spring_files.items():
        assert files_and_samples
        for file_and_sample in files_and_samples:
            sample: Sample = archive_api.status_db.get_sample_by_internal_id(
                file_and_sample.sample_internal_id
            )
            # THEN then each file should be correctly sorted on it's archive location
            assert sample.customer.data_archive_location == archive_location


def test_archive_all_non_archived_spring_files(
    archive_api: ArchiveAPI,
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
        archive_api.archive_all_non_archived_spring_files()

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
