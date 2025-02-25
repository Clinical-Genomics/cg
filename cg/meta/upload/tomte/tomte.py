"""TOMTE upload API."""

import logging
from subprocess import CalledProcessError

import rich_click as click

from cg.cli.generate.delivery_report.base import generate_delivery_report
from cg.cli.upload.scout import upload_tomte_to_scout
from cg.constants import (
    REPORT_SUPPORTED_DATA_DELIVERY,
    REPORT_SUPPORTED_WORKFLOW,
    DataDelivery,
    Workflow,
)
from cg.meta.upload.nf_analysis import NfAnalysisUploadAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class TomteUploadAPI(NfAnalysisUploadAPI):
    """Tomte upload API."""

    def __init__(self, config: CGConfig):
        super().__init__(config=config, workflow=Workflow.TOMTE)

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Uploads Tomte analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)

        # Delivery report generation
        if (
            case.data_analysis in REPORT_SUPPORTED_WORKFLOW
            and case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY
        ):
            ctx.invoke(generate_delivery_report, case_id=case.internal_id)

        self.upload_files_to_customer_inbox(case=case)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            try:
                ctx.invoke(upload_tomte_to_scout, case_id=case.internal_id)
            except CalledProcessError as error:
                LOG.error(error)
                return
        self.update_uploaded_at(analysis)
