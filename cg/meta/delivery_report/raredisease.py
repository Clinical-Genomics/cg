"""Raredisease Delivery Report API."""

from housekeeper.store.models import File

from cg.clients.chanjo2.models import CoverageMetrics
from cg.constants.housekeeper_tags import AnalysisTag
from cg.constants.report import (
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_DATA_ANALYSIS_RAREDISEASE_FIELDS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_SAMPLE_METADATA_RAREDISEASE_FIELDS,
    REQUIRED_SAMPLE_METADATA_RAREDISEASE_WGS_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_RAREDISEASE_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
)
from cg.constants.scout import ScoutUploadKey
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.meta.delivery_report.data_validators import get_million_read_pairs
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.delivery_report.metadata import RarediseaseSampleMetadataModel
from cg.models.delivery_report.report import CaseModel, ReportRequiredFields, ScoutVariantsFiles
from cg.models.delivery_report.sample import SampleModel
from cg.models.raredisease.raredisease import RarediseaseQCMetrics
from cg.store.models import Case, Sample


class RarediseaseDeliveryReportAPI(DeliveryReportAPI):
    """API to create Raredisease delivery reports."""

    def __init__(self, analysis_api: RarediseaseAnalysisAPI):
        super().__init__(analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> RarediseaseSampleMetadataModel:
        """Return Raredisease sample metadata to include in the report."""
        sample_metrics: RarediseaseQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        gene_ids: list[int] = self.analysis_api.get_gene_ids_from_scout(case.panels)
        coverage_metrics: CoverageMetrics | None = self.analysis_api.get_sample_coverage(
            case_id=case.internal_id, sample_id=sample.internal_id, gene_ids=gene_ids
        )
        return RarediseaseSampleMetadataModel(
            bait_set=self.lims_api.capture_kit(sample.internal_id),
            duplicates=sample_metrics.percent_duplicates,
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id),
            mapped_reads=round((sample_metrics.mapped_reads / sample_metrics.total_reads) * 100, 2),
            mean_target_coverage=coverage_metrics.mean_coverage if coverage_metrics else None,
            million_read_pairs=get_million_read_pairs(sample.reads),
            pct_10x=coverage_metrics.coverage_completeness_percent if coverage_metrics else None,
            sex=sample_metrics.predicted_sex_sex_check,
        )

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel = None
    ) -> bool:
        """
        Return whether the Raredisease delivery report is accredited.
        This method evaluates the accreditation status of each sample's application.
        """
        return all(sample.application.accredited for sample in samples)

    def get_scout_variants_files(self, case_id: str) -> ScoutVariantsFiles:
        """Return Raredisease files that will be uploaded to Scout."""
        snv_vcf: str | None = self.get_scout_uploaded_file_from_hk(
            case_id=case_id, scout_key=ScoutUploadKey.VCF_SNV
        )
        sv_vcf: str | None = self.get_scout_uploaded_file_from_hk(
            case_id=case_id, scout_key=ScoutUploadKey.VCF_SV
        )
        vcf_str_file: File | None = self.housekeeper_api.get_latest_file(
            bundle=case_id, tags=[AnalysisTag.VCF_STR, case_id]
        )
        vcf_str: str | None = vcf_str_file.full_path if vcf_str_file else None
        smn_tsv: str | None = self.get_scout_uploaded_file_from_hk(
            case_id=case_id, scout_key=ScoutUploadKey.SMN_TSV
        )
        return ScoutVariantsFiles(
            snv_vcf=snv_vcf,
            sv_vcf=sv_vcf,
            vcf_str=vcf_str,
            smn_tsv=smn_tsv,
        )

    @staticmethod
    def get_sample_metadata_required_fields(case: CaseModel) -> dict:
        """Return sample metadata required fields associated to a specific sample."""
        required_sample_metadata_fields = {}
        for sample in case.samples:
            required_fields = (
                REQUIRED_SAMPLE_METADATA_RAREDISEASE_WGS_FIELDS
                if SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
                in sample.application.prep_category.lower()
                else REQUIRED_SAMPLE_METADATA_RAREDISEASE_FIELDS
            )
            required_sample_metadata_fields.update({sample.id: required_fields})
        return required_sample_metadata_fields

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return dictionary with the delivery report required fields for Raredisease."""
        report_required_fields = ReportRequiredFields(
            applications=self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            case=REQUIRED_CASE_FIELDS,
            customer=REQUIRED_CUSTOMER_FIELDS,
            data_analysis=REQUIRED_DATA_ANALYSIS_RAREDISEASE_FIELDS,
            metadata=self.get_sample_metadata_required_fields(case=case),
            methods=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            report=REQUIRED_REPORT_FIELDS,
            samples=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_RAREDISEASE_FIELDS
            ),
            timestamps=self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
        )
        return report_required_fields.model_dump()
