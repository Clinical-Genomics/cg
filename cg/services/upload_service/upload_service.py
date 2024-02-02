from cg.services.slurm_service.slurm_service import SlurmService


class UploadService:
    def __init__(self, slurm_service: SlurmService):
        self.slurm_service = slurm_service
