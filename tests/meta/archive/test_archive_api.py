from pathlib import Path
from unittest import mock

import pytest
from housekeeper.store.models import File
from requests import HTTPError, Response

from cg.constants.archiving import ArchiveLocations
from cg.constants.constants import APIMethods
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.io.controller import APIRequest
from cg.meta.archive.archive import ARCHIVE_HANDLERS, FileAndSample, SpringArchiveAPI
from cg.meta.archive.ddn.constants import (
    FAILED_JOB_STATUSES,
    METADATA_LIST,
    ONGOING_JOB_STATUSES,
    JobStatus,
)
from cg.meta.archive.ddn.ddn_data_flow_client import DDNDataFlowClient
from cg.meta.archive.ddn.models import AuthToken, GetJobStatusResponse, MiriaObject
from cg.meta.archive.ddn.utils import get_metadata
from cg.meta.archive.models import ArchiveHandler, FileTransferData
from cg.models.cg_config import DataFlowConfig
from cg.store.models import Sample


def test_add_samples_to_files(spring_archive_api: SpringArchiveAPI):
    """Tests matching Files to Samples when both files have a matching sample."""
    # GIVEN a list of SPRING Files to archive
    files_to_archive: list[File] = (
        spring_archive_api.housekeeper_api.get_non_archived_spring_files()
    )

    # WHEN adding the Sample objects
    file_and_samples: list[FileAndSample] = spring_archive_api.add_samples_to_files(
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
    files_to_archive: list[File] = (
        spring_archive_api.housekeeper_api.get_non_archived_spring_files()
    )
    # GIVEN one of the files does not match the
    files_to_archive[0].version.bundle.name = "does-not-exist"
    # WHEN adding the Sample objects
    file_and_samples: list[FileAndSample] = spring_archive_api.add_samples_to_files(
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


def test_convert_into_transfer_data(
    sample_id: str, spring_archive_api: SpringArchiveAPI, ddn_dataflow_config: DataFlowConfig
):
    """Tests instantiating the correct dataclass for a sample."""
    # GIVEN file and Sample
    file_and_sample = FileAndSample(
        file=spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first(),
        sample=spring_archive_api.status_db.get_sample_by_internal_id(sample_id),
    )
    with mock.patch.object(
        DDNDataFlowClient,
        "_set_auth_tokens",
        return_value=123,
    ):
        # WHEN calling the corresponding archive method
        data_flow_client: ArchiveHandler = ARCHIVE_HANDLERS[ArchiveLocations.KAROLINSKA_BUCKET](
            config=ddn_dataflow_config
        )
    # WHEN using it to instantiate the correct class
    transferdata: list[FileTransferData] = data_flow_client.convert_into_transfer_data(
        files_and_samples=[file_and_sample],
    )

    # THEN the returned object should be of the correct type
    assert isinstance(transferdata[0], MiriaObject)


def test_call_corresponding_archiving_method(
    spring_archive_api: SpringArchiveAPI, sample_id: str, ddn_dataflow_client: DDNDataFlowClient
):
    """Tests so that the correct archiving function is used when providing a Karolinska customer."""
    # GIVEN a file to be transferred
    # GIVEN a spring_archive_api with a mocked archive function
    file_and_sample = FileAndSample(
        file=spring_archive_api.housekeeper_api.get_files(bundle=sample_id).first(),
        sample=spring_archive_api.status_db.get_sample_by_internal_id(sample_id),
    )

    with mock.patch.object(
        DDNDataFlowClient,
        "_set_auth_tokens",
        return_value=123,
    ), mock.patch.object(
        DDNDataFlowClient,
        "archive_file",
        return_value=123,
    ) as mock_request_submitter:
        # WHEN calling the corresponding archive method
        spring_archive_api.archive_file_to_location(
            file_and_sample=file_and_sample, archive_handler=ddn_dataflow_client
        )

    # THEN the correct archive function should have been called once
    mock_request_submitter.assert_called_once_with(file_and_sample=file_and_sample)


@pytest.mark.parametrize("limit", [None, -1, 0, 1])
def test_archive_all_non_archived_spring_files(
    spring_archive_api: SpringArchiveAPI,
    caplog,
    ok_miria_response,
    archive_request_json,
    header_with_test_auth_token,
    test_auth_token: AuthToken,
    sample_id: str,
    limit: int | None,
):
    """Test archiving all non-archived SPRING files for Miria customers."""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # WHEN archiving all available files
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ) as mock_request_submitter:
        spring_archive_api.archive_spring_files_and_add_archives_to_housekeeper(
            spring_file_count_limit=limit
        )

    # THEN the DDN archiving function should have been called with the correct destination and source if limit > 0
    if limit not in [0, -1]:
        sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(sample_id)
        metadata: list[dict] = get_metadata(sample)
        archive_request_json[METADATA_LIST] = metadata
        mock_request_submitter.assert_called_with(
            api_method=APIMethods.POST,
            url="some/api/files/archive",
            headers=header_with_test_auth_token,
            json=archive_request_json,
            verify=False,
        )

        # THEN all spring files for Karolinska should have an entry in the Archive table in Housekeeper while no other
        # files should have an entry
        files: list[File] = spring_archive_api.housekeeper_api.files().all()
        for file in files:
            if SequencingFileTag.SPRING in [tag.name for tag in file.tags]:
                sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(
                    file.version.bundle.name
                )
                if sample and sample.archive_location == ArchiveLocations.KAROLINSKA_BUCKET:
                    assert file.archive
    else:
        mock_request_submitter.assert_not_called()


@pytest.mark.parametrize(
    "job_status, should_date_be_set",
    [
        (JobStatus.COMPLETED, True),
        (ONGOING_JOB_STATUSES[0], False),
        (FAILED_JOB_STATUSES[0], False),
    ],
)
def test_get_archival_status(
    spring_archive_api: SpringArchiveAPI,
    ddn_dataflow_client: DDNDataFlowClient,
    caplog,
    ok_miria_job_status_response,
    archive_request_json,
    header_with_test_auth_token,
    test_auth_token: AuthToken,
    archival_job_id: int,
    job_status: JobStatus,
    should_date_be_set: bool,
):
    # GIVEN a file with an ongoing archival
    file: File = spring_archive_api.housekeeper_api.files().first()
    spring_archive_api.housekeeper_api.add_archives(files=[file], archive_task_id=archival_job_id)

    # WHEN querying the task id and getting a "COMPLETED" response
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_job_status_response,
    ), mock.patch.object(
        DDNDataFlowClient,
        "_get_job_status",
        return_value=GetJobStatusResponse(id=archival_job_id, status=job_status),
    ):
        spring_archive_api.update_ongoing_task(
            task_id=archival_job_id,
            archive_handler=ddn_dataflow_client,
            is_archival=True,
        )

    # THEN The Archive entry should have been updated
    if job_status == FAILED_JOB_STATUSES[0]:
        assert not file.archive
    else:
        assert bool(file.archive.archived_at) == should_date_be_set


@pytest.mark.parametrize(
    "job_status, should_date_be_set",
    [
        (JobStatus.COMPLETED, True),
        (ONGOING_JOB_STATUSES[0], False),
        (FAILED_JOB_STATUSES[0], False),
    ],
)
def test_get_retrieval_status(
    spring_archive_api: SpringArchiveAPI,
    ddn_dataflow_client: DDNDataFlowClient,
    caplog,
    ok_miria_job_status_response,
    archive_request_json,
    header_with_test_auth_token,
    archival_job_id: int,
    retrieval_job_id: int,
    test_auth_token,
    job_status,
    should_date_be_set,
):
    """Tests that the three different categories of retrieval statuses we have identified,
    i.e. failed, ongoing and successful, are handled correctly."""

    # GIVEN a file with an ongoing archival
    file: File = spring_archive_api.housekeeper_api.files().first()
    spring_archive_api.housekeeper_api.add_archives(files=[file], archive_task_id=archival_job_id)
    spring_archive_api.housekeeper_api.set_archive_retrieval_task_id(
        file_id=file.id, retrieval_task_id=retrieval_job_id
    )

    # WHEN querying the task id
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_job_status_response,
    ), mock.patch.object(
        DDNDataFlowClient,
        "_get_job_status",
        return_value=GetJobStatusResponse(id=retrieval_job_id, status=job_status),
    ):
        spring_archive_api.update_ongoing_task(
            task_id=retrieval_job_id,
            archive_handler=ddn_dataflow_client,
            is_archival=False,
        )

    # THEN The Archive entry should have been updated
    if job_status == FAILED_JOB_STATUSES[0]:
        assert not file.archive.retrieval_task_id
    else:
        assert bool(file.archive.retrieved_at) == should_date_be_set


def test_retrieve_case(
    spring_archive_api: SpringArchiveAPI,
    caplog,
    ok_miria_response,
    trimmed_local_path,
    local_storage_repository,
    retrieve_request_json,
    header_with_test_auth_token,
    test_auth_token,
    archival_job_id: int,
    sample_with_spring_file: str,
):
    """Test retrieving all archived SPRING files tied to a case for a Miria customer."""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.
    files: list[File] = spring_archive_api.housekeeper_api.get_files(
        bundle=sample_with_spring_file, tags=[SequencingFileTag.SPRING]
    ).all()
    for file in files:
        spring_archive_api.housekeeper_api.add_archives(
            files=[file], archive_task_id=archival_job_id
        )
        assert not file.archive.retrieval_task_id
        assert file.archive

    sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(sample_with_spring_file)

    # WHEN archiving all available files
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ) as mock_request_submitter:
        spring_archive_api.retrieve_spring_files_for_case(sample.links[0].case.internal_id)

    retrieve_request_json["pathInfo"][0]["source"] += "/" + Path(files[0].path).name

    # THEN the DDN archiving function should have been called with the correct destination and source.
    mock_request_submitter.assert_called_with(
        api_method=APIMethods.POST,
        url="some/api/files/retrieve",
        headers=header_with_test_auth_token,
        json=retrieve_request_json,
        verify=False,
    )

    # THEN the Archive entry should have a retrieval task id set
    for file in files:
        assert file.archive.retrieval_task_id


def test_retrieve_sample(
    spring_archive_api: SpringArchiveAPI,
    caplog,
    ok_miria_response,
    trimmed_local_path,
    local_storage_repository,
    retrieve_request_json,
    header_with_test_auth_token,
    test_auth_token,
    archival_job_id: int,
    sample_with_spring_file: str,
):
    """Test retrieving all archived SPRING files tied to a sample for a Miria customer."""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # GIVEN that a sample has archived spring files
    files: list[File] = spring_archive_api.housekeeper_api.get_files(
        bundle=sample_with_spring_file, tags=[SequencingFileTag.SPRING]
    ).all()
    for file in files:
        spring_archive_api.housekeeper_api.add_archives(
            files=[file], archive_task_id=archival_job_id
        )
        assert not file.archive.retrieval_task_id
        assert file.archive

    # WHEN archiving all available files
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ) as mock_request_submitter:
        spring_archive_api.retrieve_spring_files_for_sample(sample_with_spring_file)

    retrieve_request_json["pathInfo"][0]["source"] += "/" + Path(files[0].path).name

    # THEN the DDN archiving function should have been called with the correct destination and source.
    mock_request_submitter.assert_called_with(
        api_method=APIMethods.POST,
        url="some/api/files/retrieve",
        headers=header_with_test_auth_token,
        json=retrieve_request_json,
        verify=False,
    )

    # THEN the Archive entry should have a retrieval task id set
    for file in files:
        assert file.archive.retrieval_task_id


def test_retrieve_order(
    spring_archive_api: SpringArchiveAPI,
    caplog,
    ok_miria_response,
    trimmed_local_path,
    local_storage_repository,
    retrieve_request_json,
    header_with_test_auth_token,
    test_auth_token,
    archival_job_id: int,
    sample_with_spring_file: str,
):
    """Test retrieving all archived SPRING files tied to an order for a Miria customer."""
    # GIVEN a populated status_db database with two customers, one DDN and one non-DDN,
    # with the DDN customer having two samples, and the non-DDN having one sample.

    # GIVEN that a sample has archived spring files
    files: list[File] = spring_archive_api.housekeeper_api.get_files(
        bundle=sample_with_spring_file, tags=[SequencingFileTag.SPRING]
    ).all()
    for file in files:
        spring_archive_api.housekeeper_api.add_archives(
            files=[file], archive_task_id=archival_job_id
        )
        assert not file.archive.retrieval_task_id
        assert file.archive

    sample: Sample = spring_archive_api.status_db.get_sample_by_internal_id(sample_with_spring_file)

    # WHEN archiving all available files
    with mock.patch.object(
        AuthToken,
        "model_validate",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ) as mock_request_submitter:
        spring_archive_api.retrieve_spring_files_for_order(
            id_=sample.original_ticket, is_order_id=False
        )

    retrieve_request_json["pathInfo"][0]["source"] += "/" + Path(files[0].path).name

    # THEN the DDN archiving function should have been called with the correct destination and source.
    mock_request_submitter.assert_called_with(
        api_method=APIMethods.POST,
        url="some/api/files/retrieve",
        headers=header_with_test_auth_token,
        json=retrieve_request_json,
        verify=False,
    )

    # THEN the Archive entry should have a retrieval task id set
    for file in files:
        assert file.archive.retrieval_task_id


def test_delete_file_raises_http_error(
    spring_archive_api: SpringArchiveAPI,
    failed_delete_file_response: Response,
    test_auth_token: AuthToken,
    archival_job_id: int,
):
    """Tests that an HTTP error is raised when the Miria response is unsuccessful for a delete file request,
    and that the file is not removed from Housekeeper."""

    # GIVEN a spring file which is archived via Miria
    spring_file: File = spring_archive_api.housekeeper_api.files(
        tags={SequencingFileTag.SPRING, ArchiveLocations.KAROLINSKA_BUCKET}
    ).first()
    spring_file_path: str = spring_file.path
    if not spring_file.archive:
        spring_archive_api.housekeeper_api.add_archives(
            files=[spring_file], archive_task_id=archival_job_id
        )
    spring_archive_api.housekeeper_api.set_archive_archived_at(
        file_id=spring_file.id, archiving_task_id=archival_job_id
    )

    # GIVEN that the request returns a failed response
    with mock.patch.object(
        DDNDataFlowClient,
        "_get_auth_token",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=failed_delete_file_response,
    ), pytest.raises(
        HTTPError
    ):
        # WHEN trying to delete the file via Miria and in Housekeeper

        # THEN an HTTPError should be raised
        spring_archive_api.delete_file(file_path=spring_file.path)

    # THEN the file should still be in Housekeeper
    assert spring_archive_api.housekeeper_api.files(path=spring_file_path)


def test_delete_file_success(
    spring_archive_api: SpringArchiveAPI,
    ok_delete_file_response: Response,
    test_auth_token: AuthToken,
    archival_job_id: int,
):
    """Tests that given a successful response from Miria, the file is deleted and removed from Housekeeper."""

    # GIVEN a spring file which is archived via Miria
    spring_file: File = spring_archive_api.housekeeper_api.files(
        tags={SequencingFileTag.SPRING, ArchiveLocations.KAROLINSKA_BUCKET}
    ).first()
    spring_file_id: int = spring_file.id
    if not spring_file.archive:
        spring_archive_api.housekeeper_api.add_archives(
            files=[spring_file], archive_task_id=archival_job_id
        )
    spring_archive_api.housekeeper_api.set_archive_archived_at(
        file_id=spring_file.id, archiving_task_id=archival_job_id
    )

    # GIVEN that the delete request returns a successful response
    with mock.patch.object(
        DDNDataFlowClient,
        "_get_auth_token",
        return_value=test_auth_token,
    ), mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_delete_file_response,
    ):
        # WHEN trying to delete the file via Miria and in Housekeeper

        # THEN no error is raised
        spring_archive_api.delete_file(file_path=spring_file.path)

    # THEN the file is removed from Housekeeper
    assert not spring_archive_api.housekeeper_api.get_file(spring_file_id)
