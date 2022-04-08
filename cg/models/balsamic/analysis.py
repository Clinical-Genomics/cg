from typing import Dict, Union

from pydantic import BaseModel
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import (
    BalsamicMetricsBase,
    BalsamicTargetedQCMetrics,
    BalsamicWGSQCMetrics,
    BalsamicQCMetrics,
)


class BalsamicAnalysis(BaseModel):
    """BALSAMIC analysis model

    Attributes:
        config: balsamic config file attributes model
        sample_metrics: retrieved QC metrics associated to a sample
    """

    config: BalsamicConfigJSON
    sample_metrics: Dict[str, BalsamicQCMetrics]


def cast_metrics_type(
    sequencing_type: str, metrics: dict
) -> Union[BalsamicTargetedQCMetrics, BalsamicWGSQCMetrics]:
    """Cast metrics model type according to the sequencing type"""

    if metrics:
        for k, v in metrics.items():
            metrics[k] = (
                BalsamicWGSQCMetrics(**v)
                if sequencing_type == "wgs"
                else BalsamicTargetedQCMetrics(**v)
            )

    return metrics


def parse_balsamic_analysis(config: dict, metrics: list) -> BalsamicAnalysis:
    """Returns a formatted BalsamicAnalysis object"""

    sequencing_type = config["analysis"]["sequencing_type"]
    qc_metrics = dict()

    for value in metrics:
        sample_metric = BalsamicMetricsBase(**value)
        try:
            qc_metrics[sample_metric.id].update({sample_metric.name.lower(): sample_metric.value})
        except KeyError:
            qc_metrics[sample_metric.id] = {sample_metric.name.lower(): sample_metric.value}

    return BalsamicAnalysis(
        config=config,
        sample_metrics=cast_metrics_type(sequencing_type, qc_metrics),
    )
