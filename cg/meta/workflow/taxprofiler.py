"""Module for Taxprofiler Analysis API."""

import logging
from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class TaxprofilerAnalysisAPI(AnalysisAPI):
    """Handles communication between Taxprofiler processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.TAXPROFILER,
    ):
        super().__init__(config=config, pipeline=pipeline)
