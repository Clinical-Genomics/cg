"""Module for TOMTE Analysis API."""
import logging
from cg.models.cg_config import CGConfig
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.constants import Workflow

LOG = logging.getLogger(__name__)

class TomteAnalysisAPI(NfAnalysisAPI):
    """Handles communication between TOMTE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.TOMTE,
    ):
        super().__init__(config=config, workflow=workflow)
