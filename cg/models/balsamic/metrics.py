from pydantic import field_validator

from cg.models.deliverables.metric_deliverables import MetricCondition, MetricsBase
from cg.models.qc_metrics import QCMetrics


def percent_value_validation(cls, value: float) -> float:
    """Converts a raw float value to percent"""

    return value * 100


class BalsamicMetricsBase(MetricsBase):
    """BALSAMIC base metric attributes

    Attributes:
        condition: balsamic metric validation condition
    """

    condition: MetricCondition | None = None


class BalsamicQCMetrics(QCMetrics):
    """BALSAMIC common QC metrics"""

    fold_80_base_penalty: float | None = None
    mean_insert_size: float | None = None
    percent_duplication: float | None = None

    _percent_duplication: float = field_validator("percent_duplication")(percent_value_validation)


class BalsamicTargetedQCMetrics(BalsamicQCMetrics):
    """BALSAMIC targeted QC metrics"""

    mean_target_coverage: float | None = None
    median_target_coverage: float | None = None
    pct_target_bases_50x: float | None = None
    pct_target_bases_100x: float | None = None
    pct_target_bases_250x: float | None = None
    pct_target_bases_500x: float | None = None
    pct_target_bases_1000x: float | None = None
    pct_off_bait: float | None = None
    gc_dropout: float | None = None

    _pct_values: float = field_validator(
        "pct_target_bases_50x",
        "pct_target_bases_100x",
        "pct_target_bases_250x",
        "pct_target_bases_500x",
        "pct_target_bases_1000x",
        "pct_off_bait",
    )(percent_value_validation)


class BalsamicWGSQCMetrics(BalsamicQCMetrics):
    """BALSAMIC WGS QC metrics"""

    median_coverage: float | None = None
    pct_15x: float | None = None
    pct_30x: float | None = None
    pct_60x: float | None = None
    pct_100x: float | None = None
    pct_pf_reads_improper_pairs: float | None = None

    _pct_values: float = field_validator(
        "pct_15x",
        "pct_30x",
        "pct_60x",
        "pct_100x",
        "pct_pf_reads_improper_pairs",
    )(percent_value_validation)
