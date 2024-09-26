from cg.models.analysis import AnalysisModel
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicQCMetrics


class BalsamicAnalysis(AnalysisModel):
    """BALSAMIC analysis model

    Attributes:
        config: balsamic config file attributes model
        sample_metrics: retrieved QC metrics associated to a sample
    """

    config: BalsamicConfigJSON
    sample_metrics: dict[str, BalsamicQCMetrics]
