from cg.models.analysis import AnalysisModel
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicQCMetrics


class BalsamicAnalysis(AnalysisModel):
    """BALSAMIC analysis model

    Attributes:
        balsamic_config: balsamic config file attributes model
        sample_metrics: retrieved QC metrics associated to a sample
    """

    balsamic_config: BalsamicConfigJSON
    sample_metrics: dict[str, BalsamicQCMetrics]
