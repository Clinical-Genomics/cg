"""Module for the illumina post-processing service factory."""
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


class PostProcessServiceFactory:

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir


    def create_metrics_service(self) -> MetricsService:


    def create_transfer_service(self):


    def create_post_processing_service(self):
