"""RNAFUSION upload API"""

import logging

import click

from cg.cli.upload.clinical_delivery import clinical_delivery
from cg.cli.upload.scout import scout
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models

LOG = logging.getLogger(__name__)


class RnafusionUploadAPI(UploadAPI):
    """RNAFUSION upload API"""

    def __init__(self, config: CGConfig):
        self.analysis_api: RnafusionAnalysisAPI = RnafusionAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case_obj: models.Family, restart: bool) -> None:
        """Uploads RNAFUSION analysis data and files"""

        analysis_obj: models.Analysis = case_obj.analyses[0]
        self.update_upload_started_at(analysis_obj)

        # Main upload
        # ctx.invoke(clinical_delivery, case_id=case_obj.internal_id)

        # Delivery report generation
        # if case_obj.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
        #    ctx.invoke(delivery_report, case_id=case_obj.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case_obj.data_delivery:
            ctx.invoke(scout, case_id=case_obj.internal_id, re_upload=restart)

        self.update_uploaded_at(analysis_obj)
