"""NALLO upload API."""

import datetime as dt
import logging

import rich_click as click

from cg.cli.generate.delivery_report.base import generate_delivery_report
from cg.cli.upload.scout import upload_to_scout
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class NalloUploadAPI(UploadAPI):
    """NALLO upload API."""

    def __init__(self, config: CGConfig):
        self.analysis_api = NalloAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Uploads NALLO analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)
        # Delivery report generation
        if case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(generate_delivery_report, case_id=case.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(upload_to_scout, case_id=case.internal_id, re_upload=restart)
        LOG.info(
            f"Upload of case {case.internal_id} was successful. Uploaded at {dt.datetime.now()} in StatusDB"
        )

        # Clinical delivery upload
        self.upload_files_to_customer_inbox(case)

        self.update_uploaded_at(analysis=analysis)
