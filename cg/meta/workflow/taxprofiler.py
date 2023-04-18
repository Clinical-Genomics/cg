"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from cg import resources
from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig

# from cg.models.nextflow.deliverables import NextflowDeliverables, replace_dict_values
# from cg.models.taxprofiler.taxprofiler_sample import taxprofilerSample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class TaxprofilerAnalysisAPI(AnalysisAPI):
    """Handles communication between taxprofiler processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.taxprofiler,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.taxprofiler.root

    @property
    def root(self) -> str:
        return self.root_dir
