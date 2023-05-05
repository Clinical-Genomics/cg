"""Module for Taxprofiler Analysis API."""

import logging
from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.constants import Pipeline
from cg.constants.nextflow import (
    NFX_READ1_HEADER,
    NFX_READ2_HEADER,
    NFX_SAMPLE_HEADER,
    NFX_RUN_ACCESSION,
    NFX_INSTRUMENT_PLATFORM,
)
from cg.constants.taxprofiler import (
    TaxprofilerDefaults,
)
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI

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
        self.root_dir: str = config.taxprofiler.root

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    def config_case(
        self,
        case_id: str,
    ) -> None:
        """Create sample sheet file for Taxprofiler analysis."""
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        LOG.info("Generating samplesheet")
        # self.write_samplesheet(case_id, strandedness)
        # LOG.info("Samplesheet written")
