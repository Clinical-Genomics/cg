from typing import Dict

from cg.models.analysis import AnalysisModel


class BalsamicAnalysis(AnalysisModel):
    """BALSAMIC analysis model

    Attributes:
        config: balsamic config file attributes model
        sample_metrics: retrieved QC metrics associated to a sample
    """

    config: BalsamicConfigJSON
    sample_metrics: Dict[str, BalsamicQCMetrics]
