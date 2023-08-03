from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock
from urllib.parse import urljoin

import pytest
from requests import Response

from cg.constants.constants import FileFormat, APIMethods
from cg.exc import DdnDataflowAuthenticationError
from cg.io.controller import WriteStream, APIRequest
from cg.meta.archive.ddn_dataflow import (
    DESTINATION_ATTRIBUTE,
    OSTYPE,
    ROOT_TO_TRIM,
    SOURCE_ATTRIBUTE,
    DataflowEndpoints,
    DDNDataFlowClient,
    MiriaFile,
    TransferPayload,
)
from cg.models.cg_config import DDNDataFlowConfig

FUNCTION_TO_MOCK = "cg.meta.archive.ddn_dataflow.APIRequest.api_request_from_content"


def test_correct_source_root(
    local_directory: Path, miria_file: MiriaFile, trimmed_local_directory: Path
):
    """Tests the method for trimming the source directory."""

    # GIVEN a source path and a destination path

    # WHEN creating the correctly formatted dictionary
    miria_file.trim_path(attribute_to_trim=SOURCE_ATTRIBUTE)

    # THEN the destination path should be the local directory minus the /home part
    assert miria_file.source == trimmed_local_directory.as_posix()


def test_correct_destination_root(
    local_directory: Path, miria_file: MiriaFile, trimmed_local_directory: Path
):
    """Tests the method for trimming the destination directory."""

    # GIVEN a source path and a destination path
    miria_file.destination = local_directory

    # WHEN creating the correctly formatted dictionary
    miria_file.trim_path(attribute_to_trim=DESTINATION_ATTRIBUTE)

    # THEN the destination path should be the local directory minus the /home part
    assert miria_file.destination == trimmed_local_directory.as_posix()


def test_add_repositories(ddn_dataflow_config, local_directory, remote_path, miria_file: MiriaFile):
    """Tests the method for adding the repositories to the source and destination paths."""

    # GIVEN a MiriaFile object

    # WHEN adding the repositories
    miria_file.add_repositories(
        source_prefix=ddn_dataflow_config.local_storage,
        destination_prefix=ddn_dataflow_config.archive_repository,
    )

    # THEN the repositories should be prepended to the paths
    assert miria_file.source == ddn_dataflow_config.local_storage + str(local_directory)
    assert miria_file.destination == ddn_dataflow_config.archive_repository + str(remote_path)


def test_transfer_payload_dict(transfer_payload: TransferPayload):
    """Tests that the dict structure returned by TransferPayload.dict() is compatible with the
    Dataflow API."""

    # GIVEN a TransferPayload object with two MiriaFile objects

    # WHEN obtaining the dict representation
    dict_representation: dict = transfer_payload.dict()

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
    valid_config = DDNDataFlowConfig(
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


def test_set_auth_tokens(ddn_dataflow_config: DDNDataFlowConfig, ok_response: Response):
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
    ddn_dataflow_config: DDNDataFlowConfig, unauthorized_response: Response
):
    """Tests initialization of a DDNDataFlowClient when an error is returned."""

    # GIVEN a valid DDNConfig object with invalid credentials
    ddn_dataflow_config.password = "Wrong_password"

    # GIVEN a mock response with a 401 Unauthorized status code
    unauthorized_response._content = b'{"detail": "Invalid credentials"}'

    # WHEN initializing the DDNDataFlowClient class with the invalid credentials
    with mock.patch(
        "cg.meta.archive.ddn_dataflow.APIRequest.api_request_from_content",
        return_value=unauthorized_response,
    ):
        # THEN an exception should be raised
        with pytest.raises(DdnDataflowAuthenticationError):
            DDNDataFlowClient(config=ddn_dataflow_config)


def test_transfer_payload_correct_source_root(transfer_payload: TransferPayload):
    """Tests that the dict structure returned by TransferPayload.dict() is compatible with the
    Dataflow API."""

    # GIVEN a TransferPayload object with two MiriaFile objects with untrimmed source paths
    for miria_file in transfer_payload.files_to_transfer:
        assert miria_file.source.startswith(ROOT_TO_TRIM)

    # WHEN trimming the source directory
    transfer_payload.trim_paths(attribute_to_trim=SOURCE_ATTRIBUTE)

    # THEN the source directories should no longer contain /home
    for miria_file in transfer_payload.files_to_transfer:
        assert not miria_file.source.startswith(ROOT_TO_TRIM)


def test_transfer_payload_correct_destination_root(transfer_payload: TransferPayload):
    """Tests that the dict structure returned by TransferPayload.dict() is compatible with the
    Dataflow API."""

    # GIVEN a TransferPayload object with two MiriaFile objects with untrimmed destination paths
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
            "expire": new_expiration.timestamp(),
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


def test_archive_folders(
    ddn_dataflow_client: DDNDataFlowClient,
    local_directory: Path,
    remote_path: Path,
    full_remote_path: str,
    full_local_path: str,
    ok_response: Response,
):
    """Tests that the archiving function correctly formats the input and sends API request."""

    # GIVEN two paths that should be archived

    # WHEN running the archive method and providing two paths
    with mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_response,
    ) as mock_request_submitter:
        response: bool = ddn_dataflow_client.archive_folders(
            {Path(local_directory): Path(remote_path)}
        )

    # THEN a boolean response should be returned
    assert response

    # THEN the mocked submit function should have been called exactly once with correct arguments
    mock_request_submitter.assert_called_once_with(
        api_method=APIMethods.POST,
        url=urljoin(base=ddn_dataflow_client.url, url=DataflowEndpoints.ARCHIVE_FILES),
        headers=dict(ddn_dataflow_client.headers, **ddn_dataflow_client.auth_header),
        json={
            "pathInfo": [{"source": full_local_path, "destination": full_remote_path}],
            "osType": OSTYPE,
            "createFolder": False,
            "metadataList": [],
        },
    )


def test_retrieve_folders(
    ddn_dataflow_client: DDNDataFlowClient,
    local_directory: Path,
    remote_path: Path,
    full_remote_path: str,
    full_local_path: str,
    ok_response: Response,
):
    """Tests that the retrieve function correctly formats the input and sends API request."""

    # GIVEN two paths that should be retrieved

    # WHEN running the retrieve method and providing two paths
    with mock.patch.object(
        APIRequest,
        "api_request_from_content",
        return_value=ok_response,
    ) as mock_request_submitter:
        response: bool = ddn_dataflow_client.retrieve_folders(
            {Path(remote_path): Path(local_directory)}
        )

    # THEN the response returned should be true
    assert response

    # THEN the mocked submit function should have been called exactly once with correct arguments
    mock_request_submitter.assert_called_once_with(
        api_method=APIMethods.POST,
        url=urljoin(base=ddn_dataflow_client.url, url=DataflowEndpoints.RETRIEVE_FILES),
        headers=dict(ddn_dataflow_client.headers, **ddn_dataflow_client.auth_header),
        json={
            "pathInfo": [{"source": full_remote_path, "destination": full_local_path}],
            "osType": OSTYPE,
            "createFolder": False,
            "metadataList": [],
        },
    )
