from abc import ABC, abstractmethod

from cg.models.slurm.sbatch import Sbatch


class SlurmService(ABC):
    @abstractmethod
    def submit_job(self, job_config: Sbatch) -> int:
        """Submit a job and return the job id."""
        pass
