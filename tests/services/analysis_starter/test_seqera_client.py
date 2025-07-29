import pytest
import requests
from pytest_mock import MockerFixture
from requests import Response

from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import WorkflowLaunchRequest


def test_run_case(
    seqera_platform_client: SeqeraPlatformClient,
    workflow_launch_request: WorkflowLaunchRequest,
    http_workflow_launch_response: Response,
    mocker: MockerFixture,
):
    # GIVEN a workflow launch request

    # WHEN running the case using the request
    mock_submitter: mocker.MagicMock = mocker.patch.object(
        requests,
        "post",
        return_value=http_workflow_launch_response,
    )
    seqera_platform_client.run_case(workflow_launch_request)

    # THEN the request should be sent to the Seqera platform API
    mock_submitter.assert_called_once_with(
        url=f"{seqera_platform_client.base_url}/workflow/launch",
        params={"workspaceId": seqera_platform_client.workspace_id},
        headers=seqera_platform_client.auth_headers,
        json=workflow_launch_request.model_dump(),
    )


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
        seqera_platform_client.run_case(workflow_launch_request)
