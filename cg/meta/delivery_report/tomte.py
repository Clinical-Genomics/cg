"""Tomte delivery report API."""

from cg.constants import (
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_DATA_ANALYSIS_TOMTE_FIELDS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_SAMPLE_METADATA_TOMTE_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
    REQUIRED_SAMPLE_TOMTE_FIELDS,
)
from cg.meta.delivery_report.data_validators import get_million_read_pairs
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.delivery_report.metadata import TomteSampleMetadataModel
from cg.models.delivery_report.report import CaseModel, ReportRequiredFields
from cg.models.delivery_report.sample import SampleModel
from cg.models.tomte.tomte import TomteQCMetrics
from cg.store.models import Case, Sample


class TomteDeliveryReportAPI(DeliveryReportAPI):
    """API to create Tomte delivery reports."""

    def __init__(self, analysis_api: TomteAnalysisAPI):
        super().__init__(analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> TomteSampleMetadataModel:
        """Return Tomte sample metadata to include in the delivery report."""
        sample_metrics: TomteQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        return TomteSampleMetadataModel(
            bias_5_3=sample_metrics.median_5prime_to_3prime_bias,
            duplicates=sample_metrics.pct_duplication,
            dv200=self.lims_api.get_sample_dv200(sample.internal_id),
            gc_content=sample_metrics.after_filtering_gc_content,
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id),
            input_amount=self.lims_api.get_latest_rna_input_amount(sample.internal_id),
            mean_length_r1=sample_metrics.after_filtering_read1_mean_length,
            million_read_pairs=get_million_read_pairs(sample_metrics.before_filtering_total_reads),
            mrna_bases=sample_metrics.pct_mrna_bases,
            pct_adapter=sample_metrics.pct_adapter,
            pct_intergenic_bases=sample_metrics.pct_intergenic_bases,
            pct_intronic_bases=sample_metrics.pct_intronic_bases,
            pct_surviving=sample_metrics.pct_surviving,
            q20_rate=sample_metrics.after_filtering_q20_rate,
            q30_rate=sample_metrics.after_filtering_q30_rate,
            ribosomal_bases=sample_metrics.pct_ribosomal_bases,
            rin=self.lims_api.get_sample_rin(sample.internal_id),
            uniquely_mapped_reads=sample_metrics.uniquely_mapped_percent,
        )

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Return whether the Tomte delivery report is accredited."""
        return False

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return the delivery report required fields for Tomte."""
        report_required_fields = ReportRequiredFields(
            applications=self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            case=REQUIRED_CASE_FIELDS,
            customer=REQUIRED_CUSTOMER_FIELDS,
            data_analysis=REQUIRED_DATA_ANALYSIS_TOMTE_FIELDS,
            metadata=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METADATA_TOMTE_FIELDS
            ),
            methods=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            report=REQUIRED_REPORT_FIELDS,
            samples=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TOMTE_FIELDS
            ),
            timestamps=self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
        )
        return report_required_fields.model_dump()
