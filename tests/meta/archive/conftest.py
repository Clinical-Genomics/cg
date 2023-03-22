from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pytest
from requests import Response

from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData, TransferPayload, ROOT_TO_TRIM
from cg.models.cg_config import DDNConfig


@pytest.fixture(name="ddn_dataflow_config")
def fixture_ddn_dataflow_config() -> DDNConfig:
    """Returns a mock DDN Dataflow config."""
    return DDNConfig(
        database_name="test_db",
        user="test_user",
        password="DummyPassword",
        url="some/api/url.com",
        local_storage="local@storage:",
        archive_repository="archive@repisitory:",
    )


@pytest.fixture(name="ddn_dataflow_api")
def fixture_ddn_dataflow_api(ddn_dataflow_config: DDNConfig) -> DDNDataFlowApi:
    """Returns a DDNApi without tokens being set."""
    mock_ddn_auth_success_response = Response()
    mock_ddn_auth_success_response.status_code = 200
    mock_ddn_auth_success_response._content = (
        b'{"access": "test_auth_token", "refresh": "test_refresh_token", "expire": 1677649423}'
    )
    with mock.patch(
        "cg.meta.archive.ddn_dataflow.APIRequest.api_request_from_content",
        return_value=mock_ddn_auth_success_response,
    ):
        return DDNDataFlowApi(ddn_dataflow_config)


@pytest.fixture(name="transfer_data")
def fixture_transfer_data(local_directory: Path, remote_path: Path) -> TransferData:
    """Fixture of a TransferData object."""
    return TransferData(source=local_directory.as_posix(), destination=remote_path.as_posix())


@pytest.fixture(name="transfer_payload")
def fixture_transfer_payload(transfer_data: TransferData) -> TransferPayload:
    """Fixture of a TransferPayload object containing two identical TransferData object.."""
    return TransferPayload(files_to_transfer=[transfer_data, transfer_data.copy(deep=True)])


@pytest.fixture(name="remote_path")
def fixture_remote_path() -> Path:
    """Returns a mock path."""
    return Path("/some", "place")


@pytest.fixture(name="local_directory")
def fixture_local_directory() -> Path:
    """Returns a mock path with /home as its root."""
    return Path(ROOT_TO_TRIM, "other", "place")
