from pathlib import Path
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.slurm.sbatch import Sbatch
from cg.services.slurm_service.slurm_service import SlurmService


class SlurmCLIService(SlurmService):

    def __init__(self, account: str, log_dir: Path, email: str) -> None:
        self.client = SlurmAPI()
        self.account = account
        self.log_dir = log_dir
        self.email = email

    def submit_job(self, command: str, name: str) -> int:
        sbatch: Sbatch = self._create_sbatch(command=command, name=name)
        sbatch_content: str = self.client.generate_sbatch_content(sbatch)
        sbatch_path: Path = self._get_sbatch_path(name)
        return self.client.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    def _create_sbatch(self, command: str, name: str) -> Sbatch:
        return Sbatch(
            job_name=name,
            account=self.account,
            log_dir=self.log_dir,
            email=self.email,
            hours=24,
            commands=command,
        )

    def _get_sbatch_path(self, name: str) -> Path:
        return Path(self.log_dir, "{name}.sh")
