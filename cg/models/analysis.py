from pydantic.v1 import BaseModel

from cg.models.raredisease.raredisease import RarediseaseQCMetrics
from cg.models.rnafusion.rnafusion import RnafusionQCMetrics
from cg.models.taxprofiler.taxprofiler import TaxprofilerQCMetrics
from cg.models.tomte.tomte import TomteQCMetrics


class AnalysisModel(BaseModel):
    """Metadata analysis model"""

    class Config:
        arbitrary_types_allowed = True


class NextflowAnalysis(AnalysisModel):
    """Nextflow's analysis results model."""

    sample_metrics: dict[
        str, RarediseaseQCMetrics | RnafusionQCMetrics | TaxprofilerQCMetrics | TomteQCMetrics
    ]
