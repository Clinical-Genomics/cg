from typing import Any, Dict, List, Optional

from pydantic import validator

from cg.constants.subject import Gender
from cg.models.deliverables.metric_deliverables import (
    MeanInsertSize,
    MedianTargetCoverage,
    MetricsDeliverables,
    ParsedMetrics,
    SampleMetric,
    add_metric,
    add_sample_id_metrics,
)

SAMPLE_METRICS_TO_PARSE: List[str] = []


class RnafusionParsedMetrics(ParsedMetrics):
    """Defines parsed metrics"""

    predicted_sex: str = Gender.UNKNOWN
