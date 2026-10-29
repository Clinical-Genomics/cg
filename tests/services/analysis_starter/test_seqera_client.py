from unittest.mock import Mock

import pytest
import requests
from pytest_mock import MockerFixture
from requests import Response

from cg.services.analysis_starter.submitters.seqera_platform.dtos import WorkflowLaunchRequest
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_client import (
    SeqeraPlatformClient,
)


@pytest.mark.parametrize("launch_id", [None, "previous_launch_id"])
def test_run_case(
    launch_id: str | None,
    seqera_platform_client: SeqeraPlatformClient,
    workflow_launch_request: WorkflowLaunchRequest,
    http_workflow_launch_response: Response,
    mocker: MockerFixture,
):
    # GIVEN a workflow launch request
    workflow_launch_request.launch.id = launch_id

    # WHEN running the case using the request
    mock_submitter: mocker.MagicMock = mocker.patch.object(
        requests,
        "post",
        return_value=http_workflow_launch_response,
    )
    seqera_platform_client.launch_workflow(workflow_launch_request)

    # THEN the request should be sent to the Seqera platform API
    mock_submitter.assert_called_once_with(
        headers=seqera_platform_client.auth_headers,
        json=workflow_launch_request.model_dump(exclude_none=True),
        params={"workspaceId": seqera_platform_client.workspace_id},
        url=f"{seqera_platform_client.base_url}/workflow/launch",
    )

    # THEN fresh launches omit the ID and resumes include the previous launch ID
    payload: dict = mock_submitter.call_args.kwargs["json"]["launch"]
    if launch_id:
        assert payload["id"] == launch_id
    else:
        assert "id" not in payload


def test_run_case_raises_exception_on_error(
    seqera_platform_client: SeqeraPlatformClient,
    workflow_launch_request: WorkflowLaunchRequest,
    http_not_ok_response: Response,
    mocker: MockerFixture,
):
    # GIVEN a workflow launch request and a mocked response that raises an HTTP error
    mocker.patch.object(
        requests,
        "post",
        return_value=http_not_ok_response,
    )

    # WHEN running the case using the request, then it should raise an HTTPError
    with pytest.raises(requests.exceptions.HTTPError):
        seqera_platform_client.launch_workflow(workflow_launch_request)


def test_get_workflow(
    http_get_workflow_response: Response,
    seqera_platform_client: SeqeraPlatformClient,
    mocker: MockerFixture,
):
    # GIVEN a seqera platform client

    # GIVEN the seqera platform responds as expected
    mock_get: Mock = mocker.patch.object(
        requests,
        "get",
        return_value=http_get_workflow_response,
    )
    # WHEN getting the workflow
    response_json = seqera_platform_client.get_workflow("workflow_id")

    # THEN request was as expected
    mock_get.assert_called_once_with(
        headers=seqera_platform_client.auth_headers,
        params={"workspaceId": seqera_platform_client.workspace_id},
        url=f"{seqera_platform_client.base_url}/workflow/workflow_id",
    )

    # THEN the response is as expected
    assert response_json == {
        "workflow": {
            "id": "some_id",
            "runName": "case_id",
            "sessionId": "some_session_id",
        }
    }
