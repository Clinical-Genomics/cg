"""Raredisease Delivery Report API."""

from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.analysis import AnalysisModel
from cg.models.cg_config import CGConfig
from cg.models.report.sample import SampleModel


class RarediseaseReportAPI(ReportAPI):
    """API to create Raredisease delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RarediseaseAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel = None
    ) -> bool:
        """
        Return whether the Raredisease delivery report is accredited.
        This method evaluates the accreditation status of each sample's application.
        """
        return all(sample.application.accredited for sample in samples)
