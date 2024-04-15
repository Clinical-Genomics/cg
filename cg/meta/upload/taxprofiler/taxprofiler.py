"""Taxprofiler upload API."""

import datetime as dt
import logging

import click

from cg.cli.generate.report.base import generate_delivery_report
from cg.cli.upload.clinical_delivery import upload_clinical_delivery
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class TaxprofilerUploadAPI(UploadAPI):
    """Taxprofiler upload API."""

    def __init__(self, config: CGConfig):
        self.analysis_api = TaxprofilerAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Upload Taxprofiler analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)

        # Clinical delivery
        ctx.invoke(upload_clinical_delivery, case_id=case.internal_id)

        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}."
        )
        self.update_uploaded_at(analysis=analysis)
