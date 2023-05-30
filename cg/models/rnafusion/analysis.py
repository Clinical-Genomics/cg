"""Rnafusion analysis model."""
from typing import Dict

from cg.models.analysis import AnalysisModel
from cg.models.rnafusion.metrics import RnafusionQCMetrics


class RnafusionAnalysis(AnalysisModel):
    """Rnafusion analysis model.

    Attributes:
        sample_metrics: retrieved QC metrics associated to a sample
    """

    sample_metrics: Dict[str, RnafusionQCMetrics]
