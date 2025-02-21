import requests

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.submitters.seqera_platform.dtos import LaunchRequest


class SeqeraPlatformClient:
    def __init__(self, config: SeqeraPlatformConfig):
        self.base_url: str = config.base_url
        self.bearer_token: str = config.bearer_token
        self.auth_headers: dict = {"Authorization": f"Bearer {self.bearer_token}"}
        self.compute_environment_ids: dict[SlurmQos, str] = config.compute_environments
        self.workflow_ids: dict[Workflow, int] = config.workflow_ids
        self.workspace_id: int = config.workspace_id

    def get_workflow_config(self, workflow: Workflow) -> LaunchRequest:
        workflow_id: int = self.workflow_ids.get(workflow)
        url = f"{self.base_url}/pipelines/{workflow_id}/launch"
        params: dict = {"workspaceId": self.workspace_id}
        response: requests.Response = requests.get(
            url=url, headers=self.auth_headers, params=params
        )
        response.raise_for_status()
        response_dict: dict = response.json()
        response_dict["computeEnvId"] = response_dict["computeEnv"][
            "id"
        ]  # This is to make it parseable
        return LaunchRequest.model_construct(**response_dict)

    def run_case(self, request: LaunchRequest) -> str:
        url = f"{self.base_url}/workflow/launch"
        params: dict = {"workspaceId": self.workspace_id}
        response: requests.Response = requests.post(
            url=url,
            headers=self.auth_headers,
            params=params,
            json=request.model_dump(),
        )
        response.raise_for_status()
        return response.json()["workflowId"]
