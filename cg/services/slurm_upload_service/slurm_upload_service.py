import logging
from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.priority import SlurmQos
from cg.constants.slurm import (
    SLURM_UPLOAD_EXCLUDED_COMPUTE_NODES,
    SLURM_UPLOAD_MAX_HOURS,
    SLURM_UPLOAD_MEMORY,
    SLURM_UPLOAD_TASKS,
)
from cg.models.slurm.sbatch import Sbatch
from cg.services.slurm_service.slurm_service import SlurmService
from cg.services.slurm_upload_service.slurm_upload_config import SlurmUploadConfig
from cg.services.slurm_upload_service.utils import get_quality_of_service


LOG = logging.getLogger(__name__)


class SlurmUploadService:
    def __init__(
        self,
        config: SlurmUploadConfig,
        slurm_service: SlurmService,
        trailblazer_api: TrailblazerAPI,
    ):
        self.slurm_service = slurm_service
        self.trailblazer_api = trailblazer_api
        self.config = config

    def upload(self, upload_command: str, job_name: str, case_id: str):
        LOG.debug(f"Uploading case {case_id} to via SLURM with command: {upload_command}")
        analysis: TrailblazerAnalysis = self.trailblazer_api.get_latest_completed_analysis(case_id)
        job_name = f"{job_name}_{analysis.id}"
        job_config: Sbatch = self._get_job_config(command=upload_command, job_name=job_name)
        slurm_id: int = self.slurm_service.submit_job(job_config)
        self.trailblazer_api.add_upload_job_to_analysis(slurm_id=slurm_id, analysis_id=analysis.id)

    def _get_job_config(self, command: str, job_name: str) -> Sbatch:
        quality_of_service: SlurmQos = get_quality_of_service(self.config.account)
        return Sbatch(
            account=self.config.account,
            commands=command,
            email=self.config.email,
            exclude=SLURM_UPLOAD_EXCLUDED_COMPUTE_NODES,
            hours=SLURM_UPLOAD_MAX_HOURS,
            job_name=job_name,
            log_dir=self.config.log_dir,
            memory=SLURM_UPLOAD_MEMORY,
            number_tasks=SLURM_UPLOAD_TASKS,
            quality_of_service=quality_of_service,
        )
