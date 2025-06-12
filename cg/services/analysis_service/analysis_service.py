from datetime import datetime

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.store.models import Case, Analysis
from cg.store.store import Store


class AnalysisService:

    def __init__(self, analysis_client: TrailblazerAPI, status_db: Store):
        self.status_db = status_db
        self.analysis_client = analysis_client

    def add_upload_job(self, case_id: str, slurm_id: int):
        analysis: TrailblazerAnalysis = self.analysis_client.get_latest_completed_analysis(case_id)
        self.analysis_client.add_upload_job_to_analysis(slurm_id=slurm_id, analysis_id=analysis.id)

    def get_analyses_to_upload_for_workflow(self, workflow: Workflow) -> list[Analysis]:
        """
        Get all analyses that should be uploaded for a specific workflow.
        1. Get all analyses that should be uploaded for a specific workflow
        2. Check if the analysis has been uploaded and update the uploaded_at field
        """
        analysis_to_upload: list[Analysis] = []
        analyses: list[Analysis] = self.status_db.get_analyses_to_upload(workflow=workflow)
        for analysis in analyses:
            if self._has_uploaded_started(analysis) and self._is_analysis_completed(analysis):
                self.status_db.update_analysis_uploaded_at(
                    analysis_id=analysis.id, uploaded_at=datetime.now()
                )
            if not self._is_analysis_uploaded(analysis) and self._is_analysis_completed(analysis):
                analysis_to_upload.append(analysis)
        return analysis_to_upload

    @staticmethod
    def _is_analysis_uploaded(analysis: Analysis) -> bool:
        return bool(analysis.uploaded_at)

    def _is_analysis_completed(self, analysis: Analysis) -> bool:
        return self.analysis_client.is_latest_analysis_completed(case_id=analysis.case.internal_id)

    @staticmethod
    def _has_uploaded_started(analysis: Analysis) -> bool:
        return bool(analysis.upload_started_at)
