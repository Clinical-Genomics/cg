import datetime as dt
import logging

from click import Context

from cg.meta.upload.fohm.fohm import FOHMUploadAPI
from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class MutantUploadAPI(UploadAPI):

    def __init__(self, config: CGConfig):
        self.analysis_api: MutantAnalysisAPI = MutantAnalysisAPI(config)
        self.fohm_api = FOHMUploadAPI(config)
        self.gisaid_api = GisaidAPI(config)

        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: Context, case: Case, restart: bool) -> None:
        analysis: Analysis = self.status_db.get_latest_completed_analysis_for_case(case.internal_id)
        self.update_upload_started_at(analysis)
        self.gisaid_api.upload(case.internal_id)
        self.fohm_api.aggregate_delivery(case_ids=[case.internal_id])
        self.fohm_api.sync_files_sftp()
        self.fohm_api.send_mail_reports()

        if case.is_to_be_uploaded_to_customer_inbox:
            self.upload_files_to_customer_inbox(case)
        else:
            LOG.info(
                f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
            )
            self.update_uploaded_at(analysis)
