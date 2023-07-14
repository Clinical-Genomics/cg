from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest
from requests import Response

from cg.constants.constants import FileFormat
from cg.io.controller import WriteStream
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData, TransferPayload, ROOT_TO_TRIM
from cg.models.cg_config import DDNDataFlowConfig


@pytest.fixture(name="ddn_dataflow_config")
def fixture_ddn_dataflow_config(
    local_storage_repository: str, remote_storage_repository: str
) -> DDNDataFlowConfig:
    """Returns a mock DDN Dataflow config."""
    return DDNDataFlowConfig(
        database_name="test_db",
        user="test_user",
        password="DummyPassword",
        url=Path("some", "api", "url.com").as_posix(),
        local_storage=local_storage_repository,
        archive_repository=remote_storage_repository,
    )


@pytest.fixture(name="ddn_dataflow_api")
def fixture_ddn_dataflow_api(ddn_dataflow_config: DDNDataFlowConfig) -> DDNDataFlowApi:
    """Returns a DDNApi without tokens being set."""
    mock_ddn_auth_success_response = Response()
    mock_ddn_auth_success_response.status_code = 200
    mock_ddn_auth_success_response._content = WriteStream.write_stream_from_content(
        file_format=FileFormat.JSON,
        content={
            "access": "test_auth_token",
            "refresh": "test_refresh_token",
            "expire": (datetime.now() + timedelta(minutes=20)).timestamp(),
        },
    ).encode()
    with mock.patch(
        "cg.meta.archive.ddn_dataflow.APIRequest.api_request_from_content",
        return_value=mock_ddn_auth_success_response,
    ):
        return DDNDataFlowApi(ddn_dataflow_config)


@pytest.fixture(name="transfer_data")
def fixture_transfer_data(local_directory: Path, remote_path: Path) -> TransferData:
    """Return a TransferData object."""
    return TransferData(source=local_directory.as_posix(), destination=remote_path.as_posix())


@pytest.fixture(name="transfer_payload")
def fixture_transfer_payload(transfer_data: TransferData) -> TransferPayload:
    """Return a TransferPayload object containing two identical TransferData object.."""
    return TransferPayload(files_to_transfer=[transfer_data, transfer_data.copy(deep=True)])


@pytest.fixture(name="remote_path")
def fixture_remote_path() -> Path:
    """Returns a mock path."""
    return Path("/some", "place")


@pytest.fixture(name="local_directory")
def fixture_local_directory() -> Path:
    """Returns a mock path with /home as its root."""
    return Path(ROOT_TO_TRIM, "other", "place")


@pytest.fixture(name="trimmed_local_directory")
def fixture_trimmed_local_directory(local_directory: Path) -> Path:
    """Returns the trimmed local directory."""
    return Path(f"/{local_directory.relative_to(ROOT_TO_TRIM)}")


@pytest.fixture(name="local_storage_repository")
def fixture_local_storage_repository() -> str:
    """Returns a local storage repository."""
    return "local@storage:"


@pytest.fixture(name="remote_storage_repository")
def fixture_remote_storage_repository() -> str:
    """Returns a remote storage repository."""
    return "archive@repisitory:"


@pytest.fixture(name="full_remote_path")
def fixture_full_remote_path(remote_storage_repository: str, remote_path: Path) -> str:
    """Returns the merged remote repository and path."""
    return remote_storage_repository + remote_path.as_posix()


@pytest.fixture(name="full_local_path")
def fixture_full_local_path(local_storage_repository: str, trimmed_local_directory: Path) -> str:
    """Returns the merged local repository and trimmed path."""
    return local_storage_repository + trimmed_local_directory.as_posix()
