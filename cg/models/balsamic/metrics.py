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

    condition: MetricCondition | None


class BalsamicQCMetrics(BaseModel):
    """BALSAMIC common QC metrics"""

    mean_insert_size: float | None
    fold_80_base_penalty: float | None


class BalsamicTargetedQCMetrics(BalsamicQCMetrics):
    """BALSAMIC targeted QC metrics"""

    mean_target_coverage: float | None
    median_target_coverage: float | None
    percent_duplication: float | None
    pct_target_bases_50x: float | None
    pct_target_bases_100x: float | None
    pct_target_bases_250x: float | None
    pct_target_bases_500x: float | None
    pct_target_bases_1000x: float | None
    pct_off_bait: float | None
    gc_dropout: float | None

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

    median_coverage: float | None
    percent_duplication_r1: float | None
    percent_duplication_r2: float | None
    pct_15x: float | None
    pct_30x: float | None
    pct_60x: float | None
    pct_100x: float | None
    pct_pf_reads_improper_pairs: float | None

    _pct_values = validator(
        "pct_15x",
        "pct_30x",
        "pct_60x",
        "pct_100x",
        "pct_pf_reads_improper_pairs",
        allow_reuse=True,
    )(percent_value_validation)
