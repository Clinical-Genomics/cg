from typing import List

from cg.models.analysis import AnalysisModel
from cg.models.rnafusion.rnafusion_metrics_deliverables import RnafusionParsedMetrics


class RnafusionAnalysis(AnalysisModel):
    case: str
    genome_build: str
    sample_id_metrics: List[RnafusionParsedMetrics]
    rnafusion_version: str
    sample_ids: List[str]
