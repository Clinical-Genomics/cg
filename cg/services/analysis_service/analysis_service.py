from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis


class AnalysisService:

    def __init__(self, analysis_client: TrailblazerAPI):
        self.analysis_client = analysis_client

    def add_upload_job(self, case_id: str, slurm_id: int):
        analysis: TrailblazerAnalysis = self.analysis_client.get_latest_completed_analysis(case_id)
        self.analysis_client.add_upload_job_to_analysis(slurm_id=slurm_id, analysis_id=analysis.id)
