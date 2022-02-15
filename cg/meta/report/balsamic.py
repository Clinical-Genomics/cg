from datetime import datetime
import logging

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.report.api import ReportAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicReportAPI(ReportAPI):
    """API to create BALSAMIC delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.anaysis_api = analysis_api

    def get_report_data(
        self, case_id: str, analysis_date: datetime, force_report: bool = False
    ) -> dict:
        """Fetches all the data needed to generate a delivery report"""

        # TODO
        return {}
