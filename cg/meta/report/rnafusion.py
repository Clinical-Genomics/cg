"""RNAfusion delivery report API."""
from typing import Optional

from fastapi import requests

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
    Pipeline,
)
from cg.constants.constants import GenomeVersion
from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.analysis import AnalysisModel
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.models.report.report import CaseModel
from cg.models.report.sample import SampleModel
from cg.models.rnafusion.rnafusion import RnafusionAnalysis, RnafusionQCMetrics
from cg.store.models import Case, Sample


class RnafusionReportAPI(ReportAPI):
    """API to create RNAfusion delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api: RnafusionAnalysisAPI = analysis_api

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: RnafusionAnalysis
    ) -> RnafusionSampleMetadataModel:
        """Return sample metadata to include in the report."""
        sample_metrics: RnafusionQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]

        # Skip LIMS data collection if downsampled or external
        if Sample.downsampled_to or Sample.application_version.application.is_external:
            input_amount = None
            rin = None
        else:
            input_amount = (
                self.lims_api.get_latest_rna_input_amount(sample_id=sample.internal_id),
            )
            rin = self.lims_api.get_sample_rin(sample_id=sample.internal_id)

        return RnafusionSampleMetadataModel(
            bias_5_3=sample_metrics.bias_5_3,
            duplicates=sample_metrics.pct_duplication,
            gc_content=sample_metrics.after_filtering_gc_content,
            input_amount=input_amount,
            insert_size=None,
            insert_size_peak=None,
            mapped_reads=sample_metrics.reads_aligned
            * 2
            / sample_metrics.before_filtering_total_reads,
            mean_length_r1=sample_metrics.after_filtering_read1_mean_length,
            million_read_pairs=get_million_read_pairs(
                reads=sample_metrics.before_filtering_total_reads
            ),
            mrna_bases=sample_metrics.pct_mrna_bases,
            pct_adapter=sample_metrics.pct_adapter,
            pct_surviving=sample_metrics.pct_surviving,
            q20_rate=sample_metrics.after_filtering_q20_rate,
            q30_rate=sample_metrics.after_filtering_q30_rate,
            ribosomal_bases=sample_metrics.pct_ribosomal_bases,
            rin=rin,
            uniquely_mapped_reads=sample_metrics.uniquely_mapped_percent,
        )

    def get_genome_build(self, analysis_metadata: AnalysisModel) -> str:
        """Return build version of the genome reference of a specific case."""
        return GenomeVersion.hg38.value

    def get_report_accreditation(
        self, samples: list[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Checks if the report is accredited or not. Rnafusion is not an accredited workflow."""
        return False

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> Optional[str]:
        """Return file path of the uploaded to Scout file given its tag."""
        return None

    def get_template_name(self) -> str:
        """Return template name to render the delivery report."""
        return Pipeline.RNAFUSION + "_report.html"

    def get_required_fields(self, case: CaseModel) -> dict:
        """Return dictionary with the delivery report required fields for Rnafusion."""
        return {
            "report": REQUIRED_REPORT_FIELDS,
            "customer": REQUIRED_CUSTOMER_FIELDS,
            "case": REQUIRED_CASE_FIELDS,
            "applications": self.get_application_required_fields(
                case=case, required_fields=REQUIRED_APPLICATION_FIELDS
            ),
            "data_analysis": REQUIRED_DATA_ANALYSIS_RNAFUSION_FIELDS,
            "samples": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_RNAFUSION_FIELDS
            ),
            "methods": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METHODS_FIELDS
            ),
            "timestamps": self.get_timestamp_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_TIMESTAMP_FIELDS
            ),
            "metadata": self.get_sample_required_fields(
                case=case, required_fields=REQUIRED_SAMPLE_METADATA_RNAFUSION_FIELDS
            ),
        }
