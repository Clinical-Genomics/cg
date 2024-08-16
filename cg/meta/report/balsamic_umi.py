import logging

from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicUmiReportAPI(BalsamicReportAPI):
    """API to create Balsamic UMI delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: BalsamicUmiAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api: BalsamicUmiAnalysisAPI = analysis_api
