from cg.clients.slurm.slurm_cli_client import SlurmCLIClient
from cg.services.slurm_service.slurm_service import SlurmService


class SlurmCLIService(SlurmService):

    def __init__(self, client: SlurmCLIClient) -> None:
        self.client = client

    def submit_job(self, job):
        pass
