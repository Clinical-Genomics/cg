from typing import Optional

from pydantic.v1 import BaseModel, validator

from cg.models.deliverables.metric_deliverables import MetricCondition, MetricsBase


def percent_value_validation(cls, value: float) -> float:
    """Converts a raw float value to percent"""

    return value * 100


class BalsamicMetricsBase(MetricsBase):
    """BALSAMIC base metric attributes

    Attributes:
        condition: balsamic metric validation condition
    """

    condition: Optional[MetricCondition]


class BalsamicQCMetrics(BaseModel):
    """BALSAMIC common QC metrics"""

    mean_insert_size: Optional[float]
    fold_80_base_penalty: Optional[float]


class BalsamicTargetedQCMetrics(BalsamicQCMetrics):
    """BALSAMIC targeted QC metrics"""

    mean_target_coverage: Optional[float]
    median_target_coverage: Optional[float]
    percent_duplication: Optional[float]
    pct_target_bases_50x: Optional[float]
    pct_target_bases_100x: Optional[float]
    pct_target_bases_250x: Optional[float]
    pct_target_bases_500x: Optional[float]
    pct_target_bases_1000x: Optional[float]
    pct_off_bait: Optional[float]

    _pct_values = validator(
        "percent_duplication",
        "pct_target_bases_50x",
        "pct_target_bases_100x",
        "pct_target_bases_250x",
        "pct_target_bases_500x",
        "pct_target_bases_1000x",
        "pct_off_bait",
        allow_reuse=True,
    )(percent_value_validation)


class BalsamicWGSQCMetrics(BalsamicQCMetrics):
    """BALSAMIC WGS QC metrics"""

    median_coverage: Optional[float]
    percent_duplication_r1: Optional[float]
    percent_duplication_r2: Optional[float]
    pct_15x: Optional[float]
    pct_30x: Optional[float]
    pct_60x: Optional[float]
    pct_100x: Optional[float]

    _pct_values = validator(
        "pct_15x",
        "pct_30x",
        "pct_60x",
        "pct_100x",
        allow_reuse=True,
    )(percent_value_validation)
