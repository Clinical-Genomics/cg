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
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.delivery_report.metadata import TaxprofilerSampleMetadataModel
from cg.models.delivery_report.report import CaseModel, ReportRequiredFields
from cg.models.delivery_report.sample import SampleModel
from cg.store.models import Case, Sample


class TaxprofilerDeliveryReportAPI(DeliveryReportAPI):
    """API to create Taxprofiler delivery reports."""

    def __init__(self, analysis_api: TaxprofilerAnalysisAPI):
        super().__init__(analysis_api=analysis_api)

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

        report_required_fields = ReportRequiredFields(
            applications=self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            case=REQUIRED_CASE_FIELDS,
            customer=REQUIRED_CUSTOMER_FIELDS,
            data_analysis=REQUIRED_DATA_ANALYSIS_TAXPROFILER_FIELDS,
            metadata=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METADATA_TAXPROFILER_FIELDS
            ),
            methods=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            report=REQUIRED_REPORT_FIELDS,
            samples=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TAXPROFILER_FIELDS
            ),
            timestamps=self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
        )
        return report_required_fields.model_dump()
