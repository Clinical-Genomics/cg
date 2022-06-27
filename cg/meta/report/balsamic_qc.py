import logging

from cg.meta.report.balsamic import BalsamicReportAPI

from cg.meta.workflow.balsamic_qc import BalsamicQCAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicQCReportAPI(BalsamicReportAPI):
    """API to create BALSAMIC QC delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicQCAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api
