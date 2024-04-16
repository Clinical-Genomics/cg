"""NF Analysis upload API."""

import datetime as dt
import logging

import click

from cg.cli.generate.report.base import generate_delivery_report
from cg.cli.upload.clinical_delivery import upload_clinical_delivery
from cg.cli.upload.scout import upload_to_scout
from cg.constants import (
    REPORT_SUPPORTED_DATA_DELIVERY,
    REPORT_SUPPORTED_WORKFLOW,
    DataDelivery,
    Workflow,
)
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class NfAnalysisUploadAPI(UploadAPI):
    """Nf analysis upload API."""

    def __init__(self, config: CGConfig, workflow: Workflow):
        self.analysis_api: NfAnalysisAPI = NfAnalysisAPI(config, workflow)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Upload NF analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)

        # Delivery report generation
        if (
            case.data_analysis in REPORT_SUPPORTED_WORKFLOW
            and case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY
        ):
            ctx.invoke(generate_delivery_report, case_id=case.internal_id)

        # Clinical delivery
        ctx.invoke(upload_clinical_delivery, case_id=case.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(upload_to_scout, case_id=case.internal_id, re_upload=restart)
        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
        )
        self.update_uploaded_at(analysis=analysis)
