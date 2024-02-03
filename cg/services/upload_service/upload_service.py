from cg.apps.tb.api import TrailblazerAPI
from cg.models.slurm.sbatch import Sbatch
from cg.services.slurm_service.slurm_service import SlurmService
from cg.services.upload_service.upload_config import UploadConfig

UPLOAD_MAX_HOURS = 24


class UploadService:
    def __init__(
        self, slurm_service: SlurmService, trailblazer_api: TrailblazerAPI, config: UploadConfig
    ):
        self.slurm_service = slurm_service
        self.trailblazer_api = trailblazer_api
        self.config = config

    def upload(self, upload_command: str, job_name: str, analysis_id: int):
        job_config: Sbatch = self._get_job_config(command=upload_command, job_name=job_name)
        slurm_id: int = self.slurm_service.submit_job(job_config)
        self.trailblazer_api.add_upload_job_to_analysis(slurm_id=slurm_id, analysis_id=analysis_id)

    def _get_job_config(self, command: str, job_name: str) -> Sbatch:
        return Sbatch(
            account=self.config.account,
            command=command,
            job_name=job_name,
            log_dir=self.config.log_dir,
            time=UPLOAD_MAX_HOURS,
        )
