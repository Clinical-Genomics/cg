"""RNAfusion delivery report API."""
import logging
from typing import List, Optional

from cg.meta.report.field_validators import get_million_read_pairs
from cgmodels.cg.constants import Pipeline

from cg.models.report.sample import SampleModel

from cg.constants.constants import GenomeVersion

from cg.models.analysis import AnalysisModel

from cg.models.rnafusion.metrics import RnafusionQCMetrics

from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.store.models import Sample, Family

from cg.models.rnafusion.analysis import RnafusionAnalysis

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
            bias_5_3=sample_metrics.bias_5_3,
            duplicates=sample_metrics.pct_duplication,
            gc_content=sample_metrics.after_filtering_gc_content,
            input_amount=self.lims_api.get_latest_rna_input_amount(sample.internal_id),
            insert_size=None,
            insert_size_peak=None,
            mapped_reads=sample_metrics.reads_aligned / sample_metrics.before_filtering_total_reads,
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

    def get_genome_build(self, analysis_metadata: AnalysisModel) -> str:
        """Returns the build version of the genome reference of a specific case."""
        return GenomeVersion.hg38.value

    def get_report_accreditation(
        self, samples: List[SampleModel], analysis_metadata: AnalysisModel
    ) -> bool:
        """Checks if the report is accredited or not. Rnafusion is an accredited workflow."""

        return True

    def get_scout_uploaded_file_from_hk(self, case_id: str, scout_tag: str) -> Optional[str]:
        """Return the file path of the uploaded to Scout file given its tag."""
        return None

    def get_template_name(self) -> str:
        """Retrieves the template name to render the delivery report."""

        return Pipeline.RNAFUSION + "_report.html"
