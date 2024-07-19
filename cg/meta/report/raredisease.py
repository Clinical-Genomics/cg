"""Raredisease Delivery Report API."""

from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig


class RarediseaseReportAPI(ReportAPI):
    """API to create Raredisease delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RarediseaseAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
