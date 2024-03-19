from http import HTTPStatus

import pytest
from pytest_mock import MockFixture

from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.arnold.dto.create_case_request import CreateCaseRequest


@pytest.fixture
def arnold_config() -> dict:
    return {"arnold": {"api_url": "arnold_url"}}


@pytest.fixture
def arnold_client(arnold_config: dict) -> ArnoldAPIClient:
    return ArnoldAPIClient(arnold_config)


@pytest.fixture
def mock_post_request_ok(mocker: MockFixture) -> MockFixture:
    mocked_response = mocker.Mock()
    mocked_response.status_code = HTTPStatus.OK
    return mocked_response


@pytest.fixture
def error_content() -> str:
    return "Test content."


@pytest.fixture
def mock_post_request_not_found(mocker: MockFixture, error_content: str) -> MockFixture:
    mocked_response = mocker.Mock()
    mocked_response.status_code = HTTPStatus.NOT_FOUND
    mocked_response.content = error_content
    return mocked_response


@pytest.fixture
def create_case_request() -> CreateCaseRequest:
    return CreateCaseRequest(case_id="test_case", case_info={})
