"""Taxprofiler delivery report API."""

from cg.constants import (
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_DATA_ANALYSIS_TAXPROFILER_FIELDS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_SAMPLE_METADATA_TAXPROFILER_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_TAXPROFILER_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
)
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import TaxprofilerSampleMetadataModel
from cg.models.report.report import CaseModel
from cg.models.report.sample import SampleModel
from cg.store.models import Case, Sample


class TaxprofilerReportAPI(ReportAPI):
    """API to create Taxprofiler delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: TaxprofilerAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> TaxprofilerSampleMetadataModel:
        """Return Taxprofiler sample metadata to include in the delivery report."""
        return TaxprofilerSampleMetadataModel(
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id)
        )

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Return whether the Taxprofiler delivery report is accredited."""
        return False

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return the delivery report required fields for Taxprofiler."""
        return {
            "report": REQUIRED_REPORT_FIELDS,
            "customer": REQUIRED_CUSTOMER_FIELDS,
            "case": REQUIRED_CASE_FIELDS,
            "applications": self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            "data_analysis": REQUIRED_DATA_ANALYSIS_TAXPROFILER_FIELDS,
            "samples": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TAXPROFILER_FIELDS
            ),
            "methods": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            "timestamps": self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
            "metadata": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METADATA_TAXPROFILER_FIELDS
            ),
        }
