"""Tomte delivery report API."""

from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import TomteSampleMetadataModel
from cg.store.models import Case, Sample


class TomteReportAPI(ReportAPI):
    """API to create Tomte delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> TomteSampleMetadataModel:
        """Return Tomte sample metadata to include in the delivery report."""
