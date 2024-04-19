from pydantic.v1 import BaseModel

from cg.models.rnafusion.rnafusion import RnafusionQCMetrics
from cg.models.tomte.tomte import TomteQCMetrics


class AnalysisModel(BaseModel):
    """Metadata analysis model"""


class NextflowAnalysis(AnalysisModel):
    """Nextflow's analysis results model."""

    sample_metrics: dict[str, RnafusionQCMetrics | TomteQCMetrics]
