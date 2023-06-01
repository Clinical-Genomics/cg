"""RNAfusion delivery report API."""
from cg.meta.report.field_validators import get_million_read_pairs
from cg.models.rnafusion.metrics import RnafusionQCMetrics

from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.models.rnafusion.analysis import RnafusionAnalysis

from cg.store.models import Family, Sample

from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI

from cg.models.cg_config import CGConfig

from cg.meta.report.report_api import ReportAPI


class RnafusionReportAPI(ReportAPI):
    """API to create RNAfusion delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api: RnafusionAnalysisAPI = analysis_api

    def get_sample_metadata(
        self, case: Family, sample: Sample, analysis_metadata: RnafusionAnalysis
    ) -> RnafusionSampleMetadataModel:
        """Return the sample metadata to include in the report."""
        sample_metrics: RnafusionQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        return RnafusionSampleMetadataModel(
            bias_5_3=sample_metrics.bias_5_3,
            duplicates=sample_metrics.pct_duplication,
            gc_content=sample_metrics.after_filtering_gc_content,
            input_amount=self.lims_api.get_latest_rna_input_amount(sample_id=sample.internal_id),
            insert_size=None,
            insert_size_peak=None,
            mapped_reads=sample_metrics.reads_aligned / sample_metrics.before_filtering_total_reads,
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
            rin=self.lims_api.get_sample_rin(sample_id=sample.internal_id),
            uniquely_mapped_reads=sample_metrics.uniquely_mapped_percent,
        )
