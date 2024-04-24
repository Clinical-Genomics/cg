"""NF Analysis clean API."""

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


class NfAnalysisCleanAPI:
    """Nf analysis clean API."""

    def __init__(self, config: CGConfig, workflow: Workflow):
        self.analysis_api: NfAnalysisAPI = NfAnalysisAPI(config, workflow)
        super().__init__(config=config, analysis_api=self.analysis_api)
