"""RNAfusion delivery report API."""

from cg.constants import (
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_DATA_ANALYSIS_RNAFUSION_FIELDS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_SAMPLE_METADATA_RNAFUSION_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_RNAFUSION_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
    RNAFUSION_REPORT_ACCREDITED_APPTAGS,
    RNAFUSION_REPORT_MINIMUM_INPUT_AMOUNT,
)
from cg.constants.scout import ScoutUploadKey
from cg.meta.delivery_report.data_validators import (
    get_mapped_reads_fraction,
    get_million_read_pairs,
)
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.delivery_report.metadata import RnafusionSampleMetadataModel
from cg.models.delivery_report.report import CaseModel, ReportRequiredFields, ScoutVariantsFiles
from cg.models.delivery_report.sample import SampleModel
from cg.models.rnafusion.rnafusion import RnafusionQCMetrics
from cg.store.models import Case, Sample


class RnafusionDeliveryReportAPI(DeliveryReportAPI):
    """API to create Rnafusion delivery reports."""

    def __init__(self, analysis_api: RnafusionAnalysisAPI):
        super().__init__(analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> RnafusionSampleMetadataModel:
        """Return sample metadata to include in the report."""
        sample_metrics: RnafusionQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        return RnafusionSampleMetadataModel(
            bias_5_3=sample_metrics.median_5prime_to_3prime_bias,
            duplicates=sample_metrics.pct_duplication,
            dv200=self.lims_api.get_sample_dv200(sample.internal_id),
            gc_content=sample_metrics.after_filtering_gc_content,
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id),
            input_amount=self.lims_api.get_latest_rna_input_amount(sample.internal_id),
            mapped_reads=get_mapped_reads_fraction(
                mapped_reads=sample_metrics.read_pairs_examined * 2,
                total_reads=sample_metrics.before_filtering_total_reads,
            ),
            mean_length_r1=sample_metrics.after_filtering_read1_mean_length,
            million_read_pairs=get_million_read_pairs(sample_metrics.before_filtering_total_reads),
            mrna_bases=sample_metrics.pct_mrna_bases,
            pct_adapter=sample_metrics.pct_adapter,
            pct_surviving=sample_metrics.pct_surviving,
            q20_rate=sample_metrics.after_filtering_q20_rate,
            q30_rate=sample_metrics.after_filtering_q30_rate,
            ribosomal_bases=sample_metrics.pct_ribosomal_bases,
            rin=self.lims_api.get_sample_rin(sample.internal_id),
            uniquely_mapped_reads=sample_metrics.uniquely_mapped_percent,
        )

    @staticmethod
    def is_apptag_accredited(samples: list[SampleModel]) -> bool:
        """Return Rnafusion input application tag accreditation status."""
        return all(
            sample.application.tag in RNAFUSION_REPORT_ACCREDITED_APPTAGS for sample in samples
        )

    @staticmethod
    def is_input_amount_accredited(samples: list[SampleModel]) -> bool:
        """Return Rnafusion input amount accreditation status."""
        try:
            return all(
                float(sample.metadata.input_amount) >= RNAFUSION_REPORT_MINIMUM_INPUT_AMOUNT
                for sample in samples
            )
        except ValueError:
            return False

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Return whether the Rnafusion delivery report is accredited or not."""
        is_apptag_accredited: bool = self.is_apptag_accredited(samples)
        is_input_amount_accredited: bool = self.is_input_amount_accredited(samples)
        return is_apptag_accredited and is_input_amount_accredited

    def get_scout_variants_files(self, case_id: str) -> ScoutVariantsFiles:
        """Return files that will be uploaded to Scout."""
        return ScoutVariantsFiles(
            vcf_fusion=self.get_scout_uploaded_file_from_hk(
                case_id=case_id, scout_key=ScoutUploadKey.VCF_FUSION
            )
        )

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return dictionary with the delivery report required fields for Rnafusion."""
        report_required_fields = ReportRequiredFields(
            applications=self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            case=REQUIRED_CASE_FIELDS,
            customer=REQUIRED_CUSTOMER_FIELDS,
            data_analysis=REQUIRED_DATA_ANALYSIS_RNAFUSION_FIELDS,
            metadata=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METADATA_RNAFUSION_FIELDS
            ),
            methods=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            report=REQUIRED_REPORT_FIELDS,
            samples=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_RNAFUSION_FIELDS
            ),
            timestamps=self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
        )
        return report_required_fields.model_dump()
