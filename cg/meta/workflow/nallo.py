"""Module for Nallo Analysis API."""

import logging
from cg.constants import Workflow
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class NalloAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Nallo processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.NALLO,
    ):
        super().__init__(config=config, workflow=workflow)
