"""RNAFUSION upload API."""

import datetime as dt
import logging

import click

from cg.cli.upload.clinical_delivery import upload_clinical_delivery
from cg.cli.upload.scout import upload_to_scout
from cg.constants import DataDelivery
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Family

LOG = logging.getLogger(__name__)


class RnafusionUploadAPI(UploadAPI):
    """RNAFUSION upload API."""

    def __init__(self, config: CGConfig):
        self.analysis_api: RnafusionAnalysisAPI = RnafusionAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Family, restart: bool) -> None:
        """Uploads RNAFUSION analysis data and files."""

        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis)

        # Clinical delivery
        ctx.invoke(upload_clinical_delivery, case_id=case.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(upload_to_scout, case_id=case.internal_id, re_upload=restart)

        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
        )
        self.update_uploaded_at(analysis)
