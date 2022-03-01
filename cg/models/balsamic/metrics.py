from typing import Optional, List

from pydantic import BaseModel, validator

from cg.models.deliverables.metric_deliverables import MetricsBase


class MetricCondition(BaseModel):
    """BALSAMIC metric condition model

    Attributes:
        norm: validation condition
        threshold: validation cut off
    """

    norm: str
    threshold: float


class BalsamicMetricsBase(MetricsBase):
    """BALSAMIC base metric attributes

    Attributes:
        condition: balsamic metric validation condition
    """

    condition: Optional[MetricCondition]


class BalsamicQCMetrics(BaseModel):
    """BALSAMIC QC metrics"""

    mean_insert_size: Optional[float]
    percent_duplication: Optional[float]
    mean_target_coverage: Optional[float]
    median_target_coverage: Optional[float]
    pct_target_bases_50x: Optional[float]
    pct_target_bases_100x: Optional[float]
    pct_target_bases_250x: Optional[float]
    pct_target_bases_500x: Optional[float]
    pct_target_bases_1000x: Optional[float]
    pct_off_bait: Optional[float]
    fold_80_base_penalty: Optional[float]

    @validator(
        "percent_duplication",
        "pct_target_bases_50x",
        "pct_target_bases_100x",
        "pct_target_bases_250x",
        "pct_target_bases_500x",
        "pct_target_bases_1000x",
        "pct_off_bait",
    )
    def percent_value(cls, value) -> float:
        """Converts a raw float value to percent"""

        return value * 100
