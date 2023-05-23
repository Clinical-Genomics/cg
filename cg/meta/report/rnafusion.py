"""RNAfusion delivery report API."""
import logging

from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI

from cg.models.cg_config import CGConfig

from cg.meta.report.report_api import ReportAPI

LOG = logging.getLogger(__name__)


class RnafusionReportAPI(ReportAPI):
    """API to create RNAfusion delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api
