from pydantic.v1 import BaseModel

from cg.models.qc_metrics import QCMetrics


class AnalysisModel(BaseModel):
    """Metadata analysis model"""


class NextflowAnalysis(AnalysisModel):
    """Nextflow's analysis results model."""

    sample_metrics: dict[str, QCMetrics]
