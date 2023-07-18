from typing import Optional

from pydantic import BaseModel, validator

from cg.models.deliverables.metric_deliverables import MetricCondition, MetricsBase


def percent_value_validation(cls, value: float) -> float:
    """Converts a raw float value to percent"""

    return value * 100


class BalsamicMetricsBase(MetricsBase):
    """BALSAMIC base metric attributes

    Attributes:
        condition: balsamic metric validation condition
    """

    condition: Optional[MetricCondition] = None


class BalsamicQCMetrics(BaseModel):
    """BALSAMIC common QC metrics"""

    mean_insert_size: Optional[float] = None
    fold_80_base_penalty: Optional[float] = None


class BalsamicTargetedQCMetrics(BalsamicQCMetrics):
    """BALSAMIC targeted QC metrics"""

    mean_target_coverage: Optional[float] = None
    median_target_coverage: Optional[float] = None
    percent_duplication: Optional[float] = None
    pct_target_bases_50x: Optional[float] = None
    pct_target_bases_100x: Optional[float] = None
    pct_target_bases_250x: Optional[float] = None
    pct_target_bases_500x: Optional[float] = None
    pct_target_bases_1000x: Optional[float] = None
    pct_off_bait: Optional[float] = None

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

    median_coverage: Optional[float] = None
    percent_duplication_r1: Optional[float] = None
    percent_duplication_r2: Optional[float] = None
    pct_15x: Optional[float] = None
    pct_30x: Optional[float] = None
    pct_60x: Optional[float] = None
    pct_100x: Optional[float] = None

    _pct_values = validator(
        "pct_15x",
        "pct_30x",
        "pct_60x",
        "pct_100x",
        allow_reuse=True,
    )(percent_value_validation)
