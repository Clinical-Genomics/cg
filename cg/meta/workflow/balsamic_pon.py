"""Module for Balsamic PON Analysis API."""

import logging
from pathlib import Path

from cg.constants.constants import Workflow
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class BalsamicPonAnalysisAPI(BalsamicAnalysisAPI):
    """Handles communication between Balsamic PON processes and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.BALSAMIC_PON,
    ):
        super().__init__(config=config, workflow=workflow)

    def get_case_config_path(self, case_id: str) -> Path:
        """Returns the BALSAMIC PON config path."""
        return Path(self.root_dir, case_id, case_id + "_PON.json")
