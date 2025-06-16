from pydantic import field_validator
import operator

from cg.models.deliverables.metric_deliverables import MetricCondition, MetricsBase
from cg.models.qc_metrics import QCMetrics


class BalsamicMetricValue(BaseModel):
    """BALSAMIC Metric attributes"""
    value: Any
    condition: MetricCondition | None = None

    @field_validator("value", mode="before")
    @classmethod
    def convert_and_validate_percentage(cls, v, info):
        if "pct_" in info.field_name and v is not None:
            if v <= 1:
                # Assume this is a proportion and convert to percent
                v *= 100
            if not (0 <= v <= 100):
                raise ValueError(f"Percentage for {info.field_name} must be between 0 and 100.")
        return v

    def meets_condition(self) -> bool:
        """Check if the metric value meets its condition.

        Returns:
            bool: True if the value meets the condition, False otherwise.
            If no condition is set, returns True.
        """
        if not self.condition:
            return True
        qc_function = getattr(operator, self.condition.norm)
        return qc_function(self.value, self.condition.threshold)

class BalsamicWGSQCMetrics(BalsamicQCMetrics):
    """BALSAMIC WHOLE_GENOME_SEQUENCING QC metrics"""

    median_coverage: BalsamicMetricValue | None = None
    pct_15x: BalsamicMetricValue | None = None
    pct_30x: BalsamicMetricValue | None = None
    pct_60x: BalsamicMetricValue | None = None
    pct_100x: BalsamicMetricValue | None = None
    pct_pf_reads_improper_pairs: BalsamicMetricValue | None = None


class BalsamicMetricsBase(MetricsBase):
    """BALSAMIC base metric attributes

    Attributes:
        condition: balsamic metric validation condition
    """

    condition: MetricCondition | None = None


class BalsamicQCMetrics(QCMetrics):
    """BALSAMIC common QC metrics"""

    fold_80_base_penalty: BalsamicMetricValue | None = None
    mean_insert_size: BalsamicMetricValue | None = None
    percent_duplication: BalsamicMetricValue | None = None


class BalsamicTargetedQCMetrics(BalsamicQCMetrics):
    """BALSAMIC targeted QC metrics"""
    mean_target_coverage: BalsamicMetricValue | None = None
    median_target_coverage: BalsamicMetricValue | None = None
    pct_target_bases_50x: BalsamicMetricValue | None = None
    pct_target_bases_100x: BalsamicMetricValue | None = None
    pct_target_bases_250x: BalsamicMetricValue | None = None
    pct_target_bases_500x: BalsamicMetricValue | None = None
    pct_target_bases_1000x: BalsamicMetricValue | None = None
    pct_off_bait: BalsamicMetricValue | None = None
    gc_dropout: BalsamicMetricValue | None = None


class BalsamicWGSQCMetrics(BalsamicQCMetrics):
    """BALSAMIC WHOLE_GENOME_SEQUENCING QC metrics"""

    median_coverage: BalsamicMetricValue | None = None
    pct_15x: BalsamicMetricValue | None = None
    pct_30x: BalsamicMetricValue | None = None
    pct_60x: BalsamicMetricValue | None = None
    pct_100x: BalsamicMetricValue | None = None
    pct_pf_reads_improper_pairs: BalsamicMetricValue | None = None
