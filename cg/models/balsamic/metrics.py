from typing import Optional

from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated

from cg.models.deliverables.metric_deliverables import MetricCondition, MetricsBase


def convert_to_percent(value: float) -> float:
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

    mean_insert_size: Optional[float] = None
    fold_80_base_penalty: Optional[float] = None


class BalsamicTargetedQCMetrics(BalsamicQCMetrics):
    """BALSAMIC targeted QC metrics"""

    mean_target_coverage: Optional[float] = None
    median_target_coverage: Optional[float] = None
    percent_duplication: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_target_bases_50x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_target_bases_100x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_target_bases_250x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_target_bases_500x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_target_bases_1000x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_off_bait: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None


class BalsamicWGSQCMetrics(BalsamicQCMetrics):
    """BALSAMIC WGS QC metrics"""

    median_coverage: Optional[float] = None
    percent_duplication_r1: Optional[float] = None
    percent_duplication_r2: Optional[float] = None
    pct_15x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_30x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_60x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
    pct_100x: Annotated[Optional[float], BeforeValidator(convert_to_percent)] = None
