"""RNAfusion delivery report API."""
import logging

from cg.models.rnafusion.metrics import RnafusionQCMetrics

from cg.meta.report.field_validators import get_million_read_pairs

from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.models.rnafusion.analysis import RnafusionAnalysis

from cg.store.models import Family, Sample

from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI

from cg.models.cg_config import CGConfig

from cg.meta.report.report_api import ReportAPI

LOG = logging.getLogger(__name__)


class RnafusionReportAPI(ReportAPI):
    """API to create RNAfusion delivery reports."""

    def __init__(self, config: CGConfig, analysis_api: RnafusionAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)
        self.analysis_api = analysis_api

    def get_sample_metadata(
        self, case: Family, sample: Sample, analysis_metadata: RnafusionAnalysis
    ) -> RnafusionSampleMetadataModel:
        """Fetches the sample metadata to include in the report."""
        sample_metrics: RnafusionQCMetrics = analysis_metadata.sample_metrics[sample.internal_id]
        return RnafusionSampleMetadataModel(
            million_read_pairs=get_million_read_pairs(sample.reads),
            duplicates=sample_metrics.percent_duplication,
            bias_5_3=sample_metrics.bias_5_3,
            gc_content=sample_metrics.after_filtering_gc_content,
            input_amount=self.lims_api.get_latest_rna_input_amount(sample.internal_id),
            insert_size=None,
            insert_size_peak=None,
            mean_length_r1=sample_metrics.after_filtering_read1_mean_length,
            mrna_bases=sample_metrics.pct_mrna_bases,
            pct_adapter=sample_metrics.pct_adapter,
            pct_surviving=sample_metrics.pct_surviving,
            q20_rate=sample_metrics.after_filtering_q20_rate,
            q30_rate=sample_metrics.after_filtering_q30_rate,
            ribosomal_bases=sample_metrics.pct_ribosomal_bases,
            rin=self.lims_api.get_sample_rin(sample.internal_id),
            uniquely_mapped_reads=sample_metrics.uniquely_mapped,
            uniquely_mapped_reads_pct=sample_metrics.uniquely_mapped_percent,
        )
