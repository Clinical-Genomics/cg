"""Tomte delivery report API."""

from cg.meta.report.field_validators import get_million_read_pairs
from cg.meta.report.report_api import ReportAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.report.metadata import TomteSampleMetadataModel
from cg.models.tomte.tomte import TomteQCMetrics
from cg.store.models import Case, Sample


class TomteReportAPI(ReportAPI):
    """API to create Tomte delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def get_sample_metadata(
        self, case: Case, sample: Sample, analysis_metadata: NextflowAnalysis
    ) -> TomteSampleMetadataModel:
        """Return Tomte sample metadata to include in the delivery report."""
        sample_metrics: TomteQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]

        # Skip LIMS data collection if down sampled
        input_amount = None
        rin = None
        if not sample.downsampled_to:
            input_amount = self.lims_api.get_latest_rna_input_amount(sample_id=sample.internal_id)
            rin = self.lims_api.get_sample_rin(sample_id=sample.internal_id)

        return TomteSampleMetadataModel(
            bias_5_3=sample_metrics.median_5prime_to_3prime_bias,
            duplicates=sample_metrics.fraction_duplicates,
            gc_content=sample_metrics.after_filtering_gc_content,
            input_amount=input_amount,
            mean_length_r1=sample_metrics.after_filtering_read1_mean_length,
            million_read_pairs=get_million_read_pairs(
                reads=sample_metrics.before_filtering_total_reads
            ),
            mrna_bases=sample_metrics.pct_mrna_bases,
            pct_adapter=sample_metrics.pct_adapter,
            pct_intergenic_bases=sample_metrics.pct_intergenic_bases,
            pct_intronic_bases=sample_metrics.pct_intronic_bases,
            pct_surviving=sample_metrics.pct_surviving,
            q20_rate=sample_metrics.after_filtering_q20_rate,
            q30_rate=sample_metrics.after_filtering_q30_rate,
            ribosomal_bases=sample_metrics.pct_ribosomal_bases,
            rin=rin,
            uniquely_mapped_reads=sample_metrics.uniquely_mapped_percent,
        )
