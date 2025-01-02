from click import Context

from cg.meta.upload.fohm.fohm import FOHMUploadAPI
from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case


class MutantUploadAPI(UploadAPI):

    def __init__(self, config: CGConfig):
        self.analysis_api: MutantAnalysisAPI = MutantAnalysisAPI(config)
        self.fohm_api = FOHMUploadAPI(config)
        self.gsaid_api = GisaidAPI(config)

        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: Context, case: Case, restart: bool) -> None:
        latest_analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(latest_analysis)
        self.upload_files_to_customer_inbox(case)
        self.gsaid_api.upload(case.internal_id)
        self.fohm_api.aggregate_delivery(case_ids=[case.internal_id])
        self.fohm_api.sync_files_sftp()
        self.update_uploaded_at(latest_analysis)
