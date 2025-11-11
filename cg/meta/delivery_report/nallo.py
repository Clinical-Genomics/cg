"""Nallo Delivery Report API."""

from typing import cast

from cg.clients.chanjo2.models import CoverageMetrics
from cg.constants.housekeeper_tags import AnalysisTag
from cg.constants.report import (
    REQUIRED_APPLICATION_FIELDS,
    REQUIRED_CASE_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_DATA_ANALYSIS_NALLO_FIELDS,
    REQUIRED_REPORT_FIELDS,
    REQUIRED_SAMPLE_METADATA_NALLO_FIELDS,
    REQUIRED_SAMPLE_METHODS_FIELDS,
    REQUIRED_SAMPLE_NALLO_FIELDS,
    REQUIRED_SAMPLE_TIMESTAMP_FIELDS,
)
from cg.meta.delivery_report.data_validators import get_million_read_pairs
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.delivery_report.metadata import NalloSampleMetadataModel
from cg.models.delivery_report.report import CaseModel, ReportRequiredFields, ScoutVariantsFiles
from cg.models.delivery_report.sample import SampleModel
from cg.models.nallo.nallo import NalloQCMetrics
from cg.store.models import Case, Sample


class NalloDeliveryReportAPI(DeliveryReportAPI):
    """API to create Nallo delivery reports."""

    def __init__(self, analysis_api: NalloAnalysisAPI):
        super().__init__(analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> NalloSampleMetadataModel:
        """Return Nallo sample metadata to include in the report."""
        sample_metrics: NalloQCMetrics = cast(
            NalloQCMetrics, analysis_metadata.sample_metrics[sample.internal_id]
        )
        gene_ids: list[int] = self.analysis_api.get_gene_ids_from_scout(case.panels)
        coverage_metrics: CoverageMetrics | None = self.analysis_api.get_sample_coverage(
            case_id=case.internal_id, sample_id=sample.internal_id, gene_ids=gene_ids
        )
        return NalloSampleMetadataModel(
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id),
            avg_sequence_length=sample_metrics.avg_sequence_length,
            coverage_bases=sample_metrics.coverage_bases / 1_000_000_000,
            duplicates=sample_metrics.percent_duplicates,
            mean_target_coverage=coverage_metrics.mean_coverage if coverage_metrics else None,
            median_coverage=sample_metrics.median_coverage,
            million_read_pairs=get_million_read_pairs(sample.reads),
            pct_10x=coverage_metrics.coverage_completeness_percent if coverage_metrics else None,
            sex=sample_metrics.predicted_sex_sex_check,
        )

    def is_report_accredited(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel = None
    ) -> bool:
        """
        Return whether the Nallo delivery report is accredited.
        This method evaluates the accreditation status of each sample's application.
        """
        return all(sample.application.accredited for sample in samples)

    def get_scout_variants_files(self, case_id: str) -> ScoutVariantsFiles:
        """Return Nallo files that will be uploaded to Scout."""
        return ScoutVariantsFiles(
            snv_vcf=self.housekeeper_api.get_latest_file_strict(
                bundle=case_id,
                tags=[
                    AnalysisTag.VCF_SNV_CLINICAL,
                ],
            ).full_path,
            sv_vcf=self.housekeeper_api.get_latest_file_strict(
                bundle=case_id,
                tags=[
                    AnalysisTag.VCF_SV_CLINICAL,
                ],
            ).full_path,
            vcf_str=self.housekeeper_api.get_latest_file_strict(
                bundle=case_id,
                tags=[AnalysisTag.VCF_STR],
            ).full_path,
        )

    @staticmethod
    def get_sample_metadata_required_fields(case: CaseModel) -> dict:
        """Return sample metadata required fields associated to a specific sample."""
        required_sample_metadata_fields = {}
        for sample in case.samples:
            required_fields: list[str] = REQUIRED_SAMPLE_METADATA_NALLO_FIELDS
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
            data_analysis=REQUIRED_DATA_ANALYSIS_NALLO_FIELDS,
            metadata=self.get_sample_metadata_required_fields(case=case),
            methods=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            report=REQUIRED_REPORT_FIELDS,
            samples=self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_NALLO_FIELDS
            ),
            timestamps=self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
        )
        return report_required_fields.model_dump()
