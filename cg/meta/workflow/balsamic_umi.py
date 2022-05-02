"""Module for Balsamic Analysis API"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from cg.constants import DataDelivery, Pipeline
from cg.exc import BalsamicStartError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import CGConfig
from cg.store import models
from cg.utils import Process

LOG = logging.getLogger(__name__)


class BalsamicUmiAnalysisAPI(BalsamicAnalysisAPI):
    """Handles communication between BALSAMIC processes
    and the rest of CG infrastructure"""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.BALSAMIC_UMI,
    ):
        super().__init__(config=config, pipeline=pipeline)
