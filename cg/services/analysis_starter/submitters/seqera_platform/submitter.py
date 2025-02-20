from cg.constants import Workflow
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.submitter import Submitter


class SeqeraPlatformSubmitter(Submitter):

    def __init__(self, client: SeqeraPlatformClient):
        self.client = client

    def submit(self, case_config) -> str:
        """Starts a case and returns the workflow id for the job."""
        workflow: Workflow = case_config.workflow
        workflow_config = self.client.get_workflow_config(workflow)
        run_request = self._create_launch_request(
            case_config=case_config, workflow_config=workflow_config
        )
        return self.client.run_case(run_request)

    def _create_launch_request(self, case_config, workflow_config):
        pass
