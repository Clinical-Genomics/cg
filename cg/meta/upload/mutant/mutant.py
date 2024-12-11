from click import Context

from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case


class MutantUploadAPI(UploadAPI):

    def __init__(self, config: CGConfig):
        self.analysis_api: MutantAnalysisAPI = MutantAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: Context, case: Case, restart: bool) -> None:
        latest_analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(latest_analysis)
        self.upload_files_to_customer_inbox(case)
        self.update_uploaded_at(latest_analysis)
