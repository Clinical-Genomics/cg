import mock
import requests
from requests import Response

from cg.constants import Workflow
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient


def test_get_pipeline_config(
    seqera_platform_client: SeqeraPlatformClient, http_pipeline_response: Response
):
    # GIVEN a workflow configured in the Seqera Platform
    workflow = Workflow.RAREDISEASE

    # WHEN getting the Seqera pipeline config for the workflow
    with mock.patch.object(
        requests,
        "get",
        return_value=http_pipeline_response,
    ) as mock_submitter:
        seqera_platform_client.get_pipeline_config(workflow)

    mock_submitter.assert_called_once_with(
        url=f"{seqera_platform_client.base_url}/pipelines/1/launch",
        params={"workspaceId": seqera_platform_client.workspace_id},
        headers=seqera_platform_client.auth_headers,
    )
