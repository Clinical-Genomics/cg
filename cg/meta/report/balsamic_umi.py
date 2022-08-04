import logging
from typing import Optional

from cg.constants.scout_upload import BALSAMIC_UMI_CASE_TAGS
from cg.meta.report.balsamic import BalsamicReportAPI

from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicUmiReportAPI(BalsamicReportAPI):
    """API to create BALSAMIC UMI delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicUmiAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_scout_file_tags(self, scout_tag: str) -> Optional[list]:
        """Retrieves BALSAMIC UMI uploaded to scout file tags"""

        tags = BALSAMIC_UMI_CASE_TAGS.get(scout_tag)

        return list(tags) if tags else None
