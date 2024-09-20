"""TOMTE upload API."""

import logging
from subprocess import CalledProcessError

import click


from cg.cli.upload.scout import upload_tomte_to_scout
from cg.constants import DataDelivery
from cg.meta.upload.nf_analysis import NfAnalysisUploadAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class TomteUploadAPI(NfAnalysisUploadAPI):
    """MIP-RNA upload API."""

    def __init__(self, config: CGConfig):
        super().__init__(config=config)

    def upload(self, ctx: click.Context, case: Case) -> None:
        """Uploads Tomte analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)

        self.upload_files_to_customer_inbox(case=case)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            try:
                ctx.invoke(upload_tomte_to_scout, case_id=case.internal_id)
            except CalledProcessError as error:
                LOG.error(error)
                return
        self.update_uploaded_at(analysis)
