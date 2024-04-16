"""Tomte delivery report API."""

from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig


class TomteReportAPI(ReportAPI):
    """API to create Tomte delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
