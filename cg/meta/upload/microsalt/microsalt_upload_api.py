import datetime as dt
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
        analysis: Analysis = self.status_db.get_latest_completed_analysis_for_case(case.internal_id)
        self.update_upload_started_at(analysis)

        if case.is_to_be_uploaded_to_customer_inbox:
            self.upload_files_to_customer_inbox(case)
        else:
            LOG.info(
                f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
            )
            self.update_uploaded_at(analysis=analysis)
