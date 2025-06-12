from pathlib import Path
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.models.slurm.sbatch import Sbatch
from cg.services.slurm_service.slurm_service import SlurmService


class SlurmCLIService(SlurmService):
    def __init__(self) -> None:
        self.client = SlurmAPI()

    def submit_job(self, job_config: Sbatch) -> int:
        sbatch_content: str = self.client.generate_sbatch_content(job_config)
        sbatch_path: Path = self._get_sbatch_path(job_config)
        return self.client.submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    def _get_sbatch_path(self, job_config: Sbatch) -> Path:
        return Path(job_config.log_dir, f"{job_config.job_name}.sh")
