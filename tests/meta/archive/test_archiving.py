from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock
from urllib.parse import urljoin

import pytest
from requests import Response

from cg.constants.constants import APIMethods, FileFormat
from cg.exc import DdnDataflowAuthenticationError
from cg.io.controller import APIRequest, WriteStream
from cg.meta.archive.ddn.constants import (
    DESTINATION_ATTRIBUTE,
    OSTYPE,
    ROOT_TO_TRIM,
    SOURCE_ATTRIBUTE,
    DataflowEndpoints,
)
from cg.meta.archive.ddn.ddn_data_flow_client import DDNDataFlowClient
from cg.meta.archive.ddn.models import MiriaObject, TransferPayload
from cg.meta.archive.ddn.utils import get_metadata
from cg.meta.archive.models import FileAndSample
from cg.models.cg_config import DataFlowConfig
from cg.store.store import Store

FUNCTION_TO_MOCK = "cg.meta.archive.ddn.ddn_data_flow_client.APIRequest.api_request_from_content"


def test_correct_source_root(
    local_directory: Path, miria_file_archive: MiriaObject, trimmed_local_directory: Path
):
    """Tests the method for trimming the source directory."""

    # GIVEN a MiriaObject with a source path and a destination path

    # WHEN trimming the path of the source attribute
    miria_file_archive.trim_path(attribute_to_trim=SOURCE_ATTRIBUTE)

    # THEN the source path should be the local directory minus the /home part
    assert miria_file_archive.source == trimmed_local_directory.as_posix()


def test_correct_destination_root(
    local_directory: Path, miria_file_archive: MiriaObject, trimmed_local_directory: Path
):
    """Tests the method for trimming the destination directory."""

    # GIVEN a MiriaObject with a source path and a destination path
    miria_file_archive.destination = local_directory

    # WHEN trimming the path of the destination attribute
    miria_file_archive.trim_path(attribute_to_trim=DESTINATION_ATTRIBUTE)

    # THEN the destination path should be the local directory minus the /home part
    assert miria_file_archive.destination == trimmed_local_directory.as_posix()


def test_add_repositories(
    ddn_dataflow_config, local_directory, remote_path, miria_file_archive: MiriaObject
):
    """Tests the method for adding the repositories to the source and destination paths."""

    # GIVEN a MiriaObject object

    # WHEN adding the repositories
    miria_file_archive.add_repositories(
        source_prefix=ddn_dataflow_config.local_storage,
        destination_prefix=ddn_dataflow_config.archive_repository,
    )

    # THEN the repositories should be prepended to the paths
    assert miria_file_archive.source == ddn_dataflow_config.local_storage + str(local_directory)
    assert miria_file_archive.destination == ddn_dataflow_config.archive_repository + str(
        remote_path
    )


def test_transfer_payload_model_dump(transfer_payload: TransferPayload):
    """Tests that the dict structure returned by TransferPayload.dict() is compatible with the
    Dataflow API."""

    # GIVEN a TransferPayload object with two MiriaObject objects

    # WHEN obtaining the dict representation
    dict_representation: dict = transfer_payload.model_dump(by_alias=True)

    # THEN the following fields should exist
    assert dict_representation.get("pathInfo", None)
    assert dict_representation.get("osType", None)
    assert isinstance(dict_representation.get("metadataList", None), list)

    # THEN the pathInfo fields should contain source and destination fields
    assert dict_representation.get("pathInfo")[0].get("source", None)
    assert dict_representation.get("pathInfo")[0].get("destination", None)


def test_ddn_dataflow_client_initialization(
    future_date: datetime,
    local_storage_repository: str,
    remote_storage_repository: str,
    ok_response: Response,
):
    """Tests the initialization of the DDNDataFlowClient object with given an ok-response."""

    # GIVEN a valid DDNConfig object
    valid_config = DataFlowConfig(
        database_name="test_database",
        user="test_user",
        password="test_password",
        url="https://test-url.com",
        archive_repository=remote_storage_repository,
        local_storage=local_storage_repository,
    )

    # GIVEN a mock response with a 200 OK status code and valid JSON content
    ok_response._content = WriteStream.write_stream_from_content(
        content={
            "refresh": "test_refresh_token",
            "access": "test_access_token",
            "expire": future_date.timestamp(),
        },
        file_format=FileFormat.JSON,
    ).encode()

    # WHEN initializing the DDNDataFlowClient class with the valid DDNConfig object
    with mock.patch(
        FUNCTION_TO_MOCK,
        return_value=ok_response,
    ):
        ddn_dataflow_client = DDNDataFlowClient(config=valid_config)

    # THEN the DDNDataFlowClient object should be created successfully
    assert isinstance(ddn_dataflow_client, DDNDataFlowClient)


def test_set_auth_tokens(ddn_dataflow_config: DataFlowConfig, ok_response: Response):
    """Tests the functions setting the auth- and refresh token as well as the expiration date."""

    # GIVEN a valid DDNConfig object
    # GIVEN a mock response with the auth and refresh tokens
    ok_response._content = (
        b'{"access": "test_auth_token", "refresh": "test_refresh_token", "expire": 1677649423}'
    )

    # WHEN initializing the DDNDataFlowClient class with the valid DDNConfig object
    with mock.patch(
        FUNCTION_TO_MOCK,
        return_value=ok_response,
    ):
        ddn_dataflow_client = DDNDataFlowClient(config=ddn_dataflow_config)

    # THEN the auth and refresh tokens should be set correctly
    assert ddn_dataflow_client.auth_token == "test_auth_token"
    assert ddn_dataflow_client.refresh_token == "test_refresh_token"


def test_ddn_dataflow_client_initialization_invalid_credentials(
    ddn_dataflow_config: DataFlowConfig, unauthorized_response: Response
):
    """Tests initialization of a DDNDataFlowClient when an error is returned."""

    # GIVEN a valid DDNConfig object with invalid credentials
    ddn_dataflow_config.password = "Wrong_password"

    # GIVEN a mock response with a 401 Unauthorized status code
    unauthorized_response._content = b'{"detail": "Invalid credentials"}'

    # WHEN initializing the DDNDataFlowClient class with the invalid credentials
    with mock.patch(
        "cg.meta.archive.ddn.ddn_data_flow_client.APIRequest.api_request_from_content",
        return_value=unauthorized_response,
    ):
        # THEN an exception should be raised
        with pytest.raises(DdnDataflowAuthenticationError):
            DDNDataFlowClient(config=ddn_dataflow_config)


def test_transfer_payload_correct_source_root(transfer_payload: TransferPayload):
    """Tests trimming all source paths in the TransferPayload object."""
    # GIVEN a TransferPayload object with two MiriaObject objects with untrimmed source paths
    for miria_file in transfer_payload.files_to_transfer:
        assert miria_file.source.startswith(ROOT_TO_TRIM)

    # WHEN trimming the source directory
    transfer_payload.trim_paths(attribute_to_trim=SOURCE_ATTRIBUTE)

    # THEN the source directories should no longer contain /home
    for miria_file in transfer_payload.files_to_transfer:
        assert not miria_file.source.startswith(ROOT_TO_TRIM)


def test_transfer_payload_correct_destination_root(transfer_payload: TransferPayload):
    """Tests trimming all destination paths in the TransferPayload object."""

    # GIVEN a TransferPayload object with two MiriaObject objects with untrimmed destination paths
    for miria_file in transfer_payload.files_to_transfer:
        miria_file.destination = ROOT_TO_TRIM + miria_file.destination
        assert miria_file.destination.startswith(ROOT_TO_TRIM)

    # WHEN trimming the destination directories
    transfer_payload.trim_paths(attribute_to_trim=DESTINATION_ATTRIBUTE)

    # THEN the destination directories should no longer contain /home
    for miria_file in transfer_payload.files_to_transfer:
        assert not miria_file.destination.startswith(ROOT_TO_TRIM)


def test_auth_header_old_token(ddn_dataflow_client: DDNDataFlowClient, old_timestamp: datetime):
    """Tests that the refresh method is called if the auth token is too old."""

    # GIVEN a DDNDataFlowClient with an old auth token
    ddn_dataflow_client.token_expiration = old_timestamp

    # WHEN asking for the auth header
    with mock.patch.object(ddn_dataflow_client, "_refresh_auth_token") as mock_refresh_method:
        auth_header: dict = ddn_dataflow_client.auth_header

    # THEN the refresh method should have been called
    mock_refresh_method.assert_called()

    # THEN the returned dict should have the correct format and contain the current auth token
    assert auth_header.get("Authorization") == f"Bearer {ddn_dataflow_client.auth_token}"


def test_auth_header_new_token(ddn_dataflow_client: DDNDataFlowClient):
    """Tests that the refresh method is not called if the auth token is new."""

    # GIVEN a DDNDataFlowClient with a new auth token
    ddn_dataflow_client.token_expiration = datetime.now() + timedelta(minutes=20)

    # WHEN asking for the auth header
    with mock.patch.object(ddn_dataflow_client, "_refresh_auth_token") as mock_refresh_method:
        auth_header: dict = ddn_dataflow_client.auth_header

    # THEN the refresh method should not have been called
    mock_refresh_method.assert_not_called()

    # THEN the returned dict should have the correct format and contain the current auth token
    assert auth_header.get("Authorization") == f"Bearer {ddn_dataflow_client.auth_token}"


def test__refresh_auth_token(ddn_dataflow_client: DDNDataFlowClient, ok_response: Response):
    """Tests if the refresh token is correctly updated when used."""

    # GIVEN a DDNDataFlowClient with new token
    new_token: str = "new_token"
    new_expiration: datetime = datetime.now() + timedelta(minutes=30)
    ok_response._content = WriteStream.write_stream_from_content(
        content={
            "access": new_token,
            "expire": int(new_expiration.timestamp()),
        },
        file_format=FileFormat.JSON,
    ).encode()

    # WHEN refreshing the auth token
    with mock.patch(
        FUNCTION_TO_MOCK,
        return_value=ok_response,
    ):
        ddn_dataflow_client._refresh_auth_token()

    # THEN the api token and the expiration time should be updated
    assert ddn_dataflow_client.auth_token == new_token
    assert ddn_dataflow_client.token_expiration.second == new_expiration.second


def test_archive_file(
    ddn_dataflow_client: DDNDataFlowClient,
    remote_storage_repository: str,
    local_storage_repository: str,
    file_and_sample: FileAndSample,
    trimmed_local_path: str,
    ok_miria_response,
):
    """Tests that the archiving function correctly formats the input and sends API request."""

    # GIVEN two paths that should be archived
    # WHEN running the archive method and providing two paths
    with mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_miria_response,
    ) as mock_request_submitter:
        job_id: int = ddn_dataflow_client.archive_file(file_and_sample)

    # THEN an integer should be returned
    assert isinstance(job_id, int)

    # THEN the mocked submit function should have been called exactly once with correct arguments
    mock_request_submitter.assert_called_once_with(
        api_method=APIMethods.POST,
        url=urljoin(base=ddn_dataflow_client.url, url=DataflowEndpoints.ARCHIVE_FILES),
        headers=dict(ddn_dataflow_client.headers, **ddn_dataflow_client.auth_header),
        json={
            "pathInfo": [
                {
                    "source": local_storage_repository + trimmed_local_path,
                    "destination": remote_storage_repository + file_and_sample.sample.internal_id,
                }
            ],
            "osType": OSTYPE,
            "createFolder": True,
            "metadataList": get_metadata(file_and_sample.sample),
            "settings": [],
        },
        verify=False,
    )


def test_retrieve_files(
    ddn_dataflow_client: DDNDataFlowClient,
    remote_storage_repository: str,
    local_storage_repository: str,
    archive_store: Store,
    trimmed_local_path: str,
    file_and_sample: FileAndSample,
    ok_miria_response,
    retrieve_request_json,
):
    """Tests that the retrieve function correctly formats the input and sends API request."""

    # GIVEN a file and sample which is archived

    # WHEN running retrieve_files and providing a FileAndSample object
    with mock.patch.object(
        APIRequest, "api_request_from_content", return_value=ok_miria_response
    ) as mock_request_submitter:
        job_id: int = ddn_dataflow_client.retrieve_files(files_and_samples=[file_and_sample])

        # THEN an integer should be returned
    assert isinstance(job_id, int)

    # THEN the mocked submit function should have been called exactly once with correct arguments
    retrieve_request_json["pathInfo"][0]["source"] += "/" + Path(file_and_sample.file.path).name
    mock_request_submitter.assert_called_once_with(
        api_method=APIMethods.POST,
        url=urljoin(base=ddn_dataflow_client.url, url=DataflowEndpoints.RETRIEVE_FILES),
        headers=dict(ddn_dataflow_client.headers, **ddn_dataflow_client.auth_header),
        json=retrieve_request_json,
        verify=False,
    )


def test_create_transfer_request_archiving(
    ddn_dataflow_client: DDNDataFlowClient, miria_file_archive: MiriaObject
):
    """Tests creating an archiving request."""
    # GIVEN a TransferData object with an untrimmed source path, and without the source and
    # destination repositories pre-pended
    assert miria_file_archive.source.startswith(ROOT_TO_TRIM)

    # WHEN creating the archiving request
    transfer_request: TransferPayload = ddn_dataflow_client.create_transfer_request(
        [miria_file_archive], is_archiving_request=True
    )

    # THEN the source directories should no longer contain /home
    # THEN the source path should start with the local_storage prefix
    # THEN the destination path should start with the archive prefix
    assert transfer_request.files_to_transfer
    for transfer_data_archive in transfer_request.files_to_transfer:
        assert ROOT_TO_TRIM not in transfer_data_archive.source
        assert transfer_data_archive.source.startswith(ddn_dataflow_client.local_storage)
        assert transfer_data_archive.destination.startswith(ddn_dataflow_client.archive_repository)


def test_create_transfer_request_retrieve(
    ddn_dataflow_client: DDNDataFlowClient, miria_file_retrieve: MiriaObject
):
    """Tests creating a retrieve request."""
    # GIVEN a TransferData object with an untrimmed destination path, and without the source and
    # destination repositories pre-pended
    assert miria_file_retrieve.destination.startswith(ROOT_TO_TRIM)

    # WHEN creating the retrieve request
    transfer_request: TransferPayload = ddn_dataflow_client.create_transfer_request(
        [miria_file_retrieve], is_archiving_request=False
    )

    # THEN the destination directories should no longer contain /home
    # THEN the source path should start with the archive prefix
    # THEN the destination path should start with the local_storage prefix
    assert transfer_request.files_to_transfer
    for transfer_data_archive in transfer_request.files_to_transfer:
        assert ROOT_TO_TRIM not in transfer_data_archive.destination
        assert transfer_data_archive.source.startswith(ddn_dataflow_client.archive_repository)
        assert transfer_data_archive.destination.startswith(ddn_dataflow_client.local_storage)
