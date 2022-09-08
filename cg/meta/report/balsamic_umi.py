import logging

from cg.constants.scout_upload import BALSAMIC_UMI_CASE_TAGS
from cg.meta.report.balsamic import BalsamicReportAPI

from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicUmiReportAPI(BalsamicReportAPI):
    """API to create BALSAMIC UMI delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: BalsamicUmiAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_upload_case_tags(self) -> dict:
        """Retrieves BALSAMIC UMI upload case tags."""

        return BALSAMIC_UMI_CASE_TAGS
