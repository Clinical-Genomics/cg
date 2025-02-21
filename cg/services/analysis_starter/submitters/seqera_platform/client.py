import requests

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.models.cg_config import SeqeraPlatformConfig


class SeqeraPlatformClient:
    def __init__(self, config: SeqeraPlatformConfig):
        self.base_url: str = config.base_url
        self.bearer_token: str = config.bearer_token
        self.compute_environment_ids: dict[SlurmQos, str] = config.compute_environments
        self.workflow_ids: dict[Workflow, int] = config.workflow_ids
        self.workspace_id: int = config.workspace_id

    def get_workflow_config(self, workflow: Workflow) -> dict:
        workflow_id: int = self.workflow_ids.get(workflow)
        url = f"{self.base_url}/pipelines/{workflow_id}/launch"
        params: dict = {"workspaceId": self.workspace_id}
        response: requests.Response = requests.get(
            url=url, headers={"Authorization": f"Bearer {self.bearer_token}"}, params=params
        )
        response.raise_for_status()
        return response.json()

    def run_case(self, request) -> dict:
        url = f"{self.base_url}/workflow/launch"
        params: dict = {"workspaceId": self.workspace_id}
        response: requests.Response = requests.post(
            url=url,
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            params=params,
            json=request,
        )
        response.raise_for_status()
        return response.json()
