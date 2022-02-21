import logging

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.report.api import ReportAPI
from cg.models.cg_config import CGConfig
from cg.models.report.sample import MetadataModel
from cg.store import models

LOG = logging.getLogger(__name__)


class BalsamicReportAPI(ReportAPI):
    """API to create BALSAMIC delivery reports"""

    def __init__(self, config: CGConfig, analysis_api: BalsamicAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.anaysis_api = analysis_api

    def get_metadata(self, sample: models.Sample, case: models.Family) -> MetadataModel:
        """Fetches the sample metadata to include in the report"""

        # TODO
        pass

    def get_data_analysis_type(self, case: models.Family) -> str:
        """Retrieves the data analysis type carried out"""

        # TODO
        pass

    def get_genome_build(self, case: models.Family) -> str:
        """Returns the build version of the genome reference of a specific case"""

        # TODO
        pass
