import logging

from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


class NfAnalysisAPI(AnalysisAPI):
    """
    Parent class for handling nf-core analyses.
    """

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.pipeline = pipeline
