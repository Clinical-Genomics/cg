from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.priority import SlurmQos
from cg.models.slurm.sbatch import Sbatch
from cg.services.slurm_service.slurm_service import SlurmService
from cg.services.slurm_upload_service.slurm_upload_config import SlurmUploadConfig
from cg.services.slurm_upload_service.utils import get_quality_of_service

UPLOAD_MEMORY = 1
UPLOAD_MAX_HOURS = 24
EXCLUDED_COMPUTE_NODES = "--exclude=gpu-compute-0-[0-1],cg-dragen"


class SlurmUploadService:
    def __init__(
        self,
        slurm_service: SlurmService,
        trailblazer_api: TrailblazerAPI,
        config: SlurmUploadConfig,
    ):
        self.slurm_service = slurm_service
        self.trailblazer_api = trailblazer_api
        self.config = config

    def upload(self, upload_command: str, job_name: str, case_id: str):
        analysis: TrailblazerAnalysis = self.trailblazer_api.get_latest_analysis(case_id)
        job_config: Sbatch = self._get_job_config(command=upload_command, job_name=job_name)
        slurm_id: int = self.slurm_service.submit_job(job_config)
        self.trailblazer_api.add_upload_job_to_analysis(slurm_id=slurm_id, analysis_id=analysis.id)

    def _get_job_config(self, command: str, job_name: str) -> Sbatch:
        quality_of_service: SlurmQos = get_quality_of_service(self.config.account)
        return Sbatch(
            account=self.config.account,
            command=command,
            job_name=job_name,
            log_dir=self.config.log_dir,
            time=UPLOAD_MAX_HOURS,
            quality_of_service=quality_of_service,
            exclude=EXCLUDED_COMPUTE_NODES,
            memory=UPLOAD_MEMORY,
        )
