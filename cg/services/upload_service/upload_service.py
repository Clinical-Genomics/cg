from cg.apps.tb.api import TrailblazerAPI
from cg.services.slurm_service.slurm_service import SlurmService


class UploadService:
    def __init__(self, slurm_service: SlurmService, trailblazer_api: TrailblazerAPI):
        self.slurm_service = slurm_service
        self.trailblazer_api = trailblazer_api

    def upload(self, upload_command: str, name: str, analysis_id: int):
        slurm_id: int = self.slurm_service.submit_job(command=upload_command, name=name)
        self.trailblazer_api.add_upload_job_to_analysis(slurm_id=slurm_id, analysis_id=analysis_id)
