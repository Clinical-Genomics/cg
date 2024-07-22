"""Raredisease Delivery Report API."""

from cg.clients.chanjo2.models import CoverageData
from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.analysis import AnalysisModel, NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.raredisease.raredisease import RarediseaseQCMetrics
from cg.models.report.metadata import RarediseaseSampleMetadataModel
from cg.models.report.sample import SampleModel
from cg.store.models import Case, Sample


class RarediseaseReportAPI(ReportAPI):
    """API to create Raredisease delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RarediseaseAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> RarediseaseSampleMetadataModel:
        """Return Raredisease sample metadata to include in the report."""
        sample_metrics: RarediseaseQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        coverage_data: CoverageData | None = self.analysis_api.get_sample_coverage(
            sample_id=sample.internal_id, panels=case.panels
        )
        return RarediseaseSampleMetadataModel(
            bait_set=self.lims_api.capture_kit(sample.internal_id),
            duplicates=sample_metrics.percent_duplicates,
            initial_qc=self.lims_api.has_sample_passed_initial_qc(sample.internal_id),
            mapped_reads=sample_metrics.mapped_reads / sample_metrics.total_reads,
            mean_target_coverage=coverage_data.mean_coverage if coverage_data else None,
            million_read_pairs=get_million_read_pairs(sample.reads),
            pct_10x=coverage_data.coverage_completeness_percent if coverage_data else None,
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
