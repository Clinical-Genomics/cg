import logging

import rich_click as click


from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.microsalt.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class MicrosaltUploadAPI(UploadAPI):
    def __init__(self, config: CGConfig):
        self.analysis_api = MicrosaltAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Uploads MicroSALT analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis)

        self.upload_files_to_customer_inbox(case)
        self.update_uploaded_at(analysis=analysis)
