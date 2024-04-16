from pydantic.v1 import BaseModel

from cg.models.rnafusion.rnafusion import RnafusionQCMetrics


class AnalysisModel(BaseModel):
    """Metadata analysis model"""


class QCMetrics(BaseModel):
    """QC metrics analysis model."""


class NextflowAnalysis(AnalysisModel):
    """Nextflow's analysis results model."""

    sample_metrics: dict[str, RnafusionQCMetrics]
