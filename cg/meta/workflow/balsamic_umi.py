"""Module for Balsamic UMI Analysis API."""

import logging

from cg.constants import Workflow
from cg.constants.scout import BALSAMIC_UMI_CASE_TAGS
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicUmiAnalysisAPI(BalsamicAnalysisAPI):
    """Handles communication between BALSAMIC processes
    and the rest of CG infrastructure"""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.BALSAMIC_UMI,
    ):
        super().__init__(config=config, workflow=workflow)

    def get_scout_upload_case_tags(self) -> dict:
        """Return Balsamic UMI Scout upload case tags."""
        return BALSAMIC_UMI_CASE_TAGS
