"""Module to test the arnold api client."""

import pytest
import requests
from pytest_mock import MockFixture

from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.arnold.dto.create_case_request import CreateCaseRequest
from cg.clients.arnold.exceptions import ArnoldClientError


def test_create_case_successful(
    mocker: MockFixture,
    arnold_client: ArnoldAPIClient,
    create_case_request: CreateCaseRequest,
    mock_post_request_ok: MockFixture,
):
    # GIVEN a mocked response from the requests.post method that is successful
    mocked_post = mocker.patch.object(requests, "post")
    mocked_post.return_value = mock_post_request_ok

    # WHEN creating a case
    arnold_client.create_case(create_case_request)

    # THEN  a case request is sent
    mocked_post.assert_called_once_with(
        f"{arnold_client.api_url}/case/", data=create_case_request.model_dump_json(), verify=True
    )


def test_create_case_not_successful(
    mocker: MockFixture,
    arnold_client: ArnoldAPIClient,
    create_case_request: CreateCaseRequest,
    mock_post_request_not_found: MockFixture,
    error_content: str,
):
    # GIVEN a mocked response from the requests.post method that is not successful
    mocked_post = mocker.patch.object(requests, "post")
    mocked_post.return_value = mock_post_request_not_found

    # WHEN creating a case

    # THEN the request raises an error
    with pytest.raises(ArnoldClientError):
        arnold_client.create_case(create_case_request)
