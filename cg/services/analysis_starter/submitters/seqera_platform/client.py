import logging

import requests

from cg.constants.priority import SlurmQos
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.submitters.seqera_platform.dtos import WorkflowLaunchRequest

LOG = logging.getLogger(__name__)


class SeqeraPlatformClient:
    def __init__(self, config: SeqeraPlatformConfig):
        self.base_url: str = config.base_url
        self.bearer_token: str = config.bearer_token
        self.auth_headers: dict = {"Authorization": f"Bearer {self.bearer_token}"}
        self.compute_environment_ids: dict[SlurmQos, str] = config.compute_environments
        self.workspace_id: int = config.workspace_id

    def run_case(self, request: WorkflowLaunchRequest) -> str:
        """Launches a case from the request and returns the workflow ID."""
        url = f"{self.base_url}/workflow/launch"
        params: dict = {"workspaceId": self.workspace_id}
        LOG.debug(
            f"Sending request body {request.model_dump()} \n Headers: {self.auth_headers} \n Params: {params}"
        )
        response: requests.Response = requests.post(
            url=url,
            headers=self.auth_headers,
            params=params,
            json=request.model_dump(),
        )
        response.raise_for_status()
        return response.json()["workflowId"]
