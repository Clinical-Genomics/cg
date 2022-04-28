from typing import List

from cg.models.analysis import AnalysisModel
from cg.models.mip.mip_metrics_deliverables import MIPParsedMetrics


class MipAnalysis(AnalysisModel):
    case: str
    genome_build: str
    sample_id_metrics: List[MIPParsedMetrics]
    mip_version: str
    rank_model_version: str
    sample_ids: List[str]
    sv_rank_model_version: str
