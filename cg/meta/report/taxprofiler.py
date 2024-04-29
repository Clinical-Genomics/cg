"""Taxprofiler delivery report API."""

from cg.constants import (
    REQUIRED_REPORT_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_SAMPLE_TAXPROFILER_FIELDS,
    REQUIRED_SAMPLE_METADATA_TAXPROFILER_FIELDS,
    REQUIRED_DATA_ANALYSIS_TAXPROFILER_FIELDS,
)
from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.analysis import NextflowAnalysis, AnalysisModel
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import TaxprofilerSampleMetadataModel
from cg.models.report.report import CaseModel
from cg.models.report.sample import SampleModel
from cg.models.taxprofiler.taxprofiler import TaxprofilerQCMetrics
from cg.store.models import Case, Sample


class TaxprofilerReportAPI(ReportAPI):
    """API to create Taxprofiler delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: TaxprofilerAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> TaxprofilerSampleMetadataModel:
        """Return Taxprofiler sample metadata to include in the delivery report."""
        sample_metrics: TaxprofilerQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        return TaxprofilerSampleMetadataModel(
            average_read_length=sample_metrics.average_length,
            duplicates=sample_metrics.pct_duplication,
            gc_content=sample_metrics.after_filtering_gc_content,
            input_amount=self.lims_api.get_latest_rna_input_amount(sample.internal_id),
            mapped_reads=get_million_read_pairs(sample_metrics.reads_mapped),
            mean_length_r1=sample_metrics.after_filtering_read1_mean_length,
            mean_length_r2=sample_metrics.after_filtering_read2_mean_length,
            million_read_pairs=get_million_read_pairs(sample_metrics.raw_total_sequences),
            million_read_pairs_after_filtering=get_million_read_pairs(
                sample_metrics.after_filtering_total_reads
            ),
            rin=self.lims_api.get_sample_rin(sample.internal_id),
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
