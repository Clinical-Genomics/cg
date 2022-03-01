from typing import Dict

from pydantic import BaseModel

from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicQCMetrics, BalsamicMetricsBase


class BalsamicAnalysis(BaseModel):
    """BALSAMIC analysis model

    Attributes:
        config: balsamic config file attributes model
        sample_metrics: retrieved QC metrics associated to a sample
    """

    config: BalsamicConfigJSON
    sample_metrics: Dict[str, BalsamicQCMetrics]


def parse_balsamic_analysis(config: dict, metrics: list) -> BalsamicAnalysis:
    """Returns a formatted BalsamicAnalysis object"""

    qc_metrics = dict()
    for v in metrics:
        sample_metric = BalsamicMetricsBase(**v)
        try:
            qc_metrics[sample_metric.id].update({sample_metric.name.lower(): sample_metric.value})
        except KeyError:
            qc_metrics[sample_metric.id] = {sample_metric.name.lower(): sample_metric.value}

    return BalsamicAnalysis(config=config, sample_metrics=qc_metrics)
