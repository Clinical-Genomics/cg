import operator
from typing import Any, Callable

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from cg.constants import PRECISION
from cg.exc import CgError, MetricsQCError
from cg.models.qc_metrics import QCMetrics


def _get_metric_per_sample_id(sample_id: str, metric_objs: list) -> Any:
    """Get metric for a sample_id from metric object"""
    for metric in metric_objs:
        if sample_id == metric.sample_id:
            return metric


def add_metric(name: str, values: dict) -> list[Any]:
    """Add metric to list of objects"""
    found_metrics: list = []
    raw_metrics: list = values.get("metrics_")
    metrics_validator: dict[str, Any] = values.get("metric_to_get_")
    for metric in raw_metrics:
        if name == metric.name and metric.name in metrics_validator:
            found_metrics.append(
                metrics_validator[metric.name](
                    sample_id=metric.id, step=metric.step, value=metric.value
                )
            )
    return found_metrics


def add_sample_id_metrics(parsed_metric: Any, values: dict) -> list[Any]:
    """Add parsed sample_id metrics gathered from all metrics to list"""
    sample_ids: set = values.get("sample_ids")
    sample_id_metrics: list = []
    metric_per_sample_id_map: dict = {}
    for metric_name in values.get("sample_metric_to_parse"):
        metric_per_sample_id_map.update({metric_name: values.get(metric_name)})
    for sample_id in sample_ids:
        metric_per_sample_id: dict = {"sample_id": sample_id}
        for metric_name, metric_objs in metric_per_sample_id_map.items():
            sample_metric: Any = _get_metric_per_sample_id(
                sample_id=sample_id, metric_objs=metric_objs
            )
            if sample_metric.value:
                metric_per_sample_id[metric_name]: Any = sample_metric.value
                metric_per_sample_id[metric_name + "_step"]: str = sample_metric.step
        sample_id_metrics.append(parsed_metric(**metric_per_sample_id))
    return sample_id_metrics


class MetricCondition(BaseModel):
    """Metric condition model

    Attributes:
        norm: validation condition
        threshold: validation cut off
    """

    norm: str
    threshold: float | str

    @field_validator("norm")
    @classmethod
    def validate_operator(cls, norm: str) -> str:
        """Validate that an operator is accepted."""
        try:
            getattr(operator, norm)
        except AttributeError as error:
            raise CgError(
                f"{norm} is not an accepted operator for QC metric conditions."
            ) from error
        return norm


class MetricsBase(BaseModel):
    """Definition for elements in deliverables metrics file."""

    header: str | None = None
    id: str
    input: str
    name: str
    step: str
    value: Any
    condition: MetricCondition | None = None


class SampleMetric(BaseModel):
    """Define base attribute for sample metrics"""

    sample_id: str
    step: str


class MeanInsertSize(SampleMetric):
    """Definition of insert size metric"""

    value: float

    @field_validator("value")
    @classmethod
    def convert_mean_insert_size(cls, value) -> int:
        """Convert raw value from float to int"""
        return int(value)


class MedianTargetCoverage(SampleMetric):
    """Definition of median target coverage"""

    value: int


class ParsedMetrics(QCMetrics):
    """Defines parsed metrics"""

    sample_id: str
    mean_insert_size: int
    mean_insert_size_step: str
    median_target_coverage: int
    median_target_coverage_step: str


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics_: list[MetricsBase] = Field(list[MetricsBase], alias="metrics")
    sample_ids: set | None = None

    @field_validator("sample_ids")
    @classmethod
    def set_sample_ids(cls, _,  info: ValidationInfo) -> set:
        """Set sample_ids gathered from all metrics"""
        sample_ids: list = []
        raw_metrics: list = info.data.get("metrics_")
        for metric in raw_metrics:
            sample_ids.append(metric.id)
        return set(sample_ids)


class MetricsDeliverablesCondition(BaseModel):
    """Specification for a metric deliverables file with conditions sets."""

    metrics: list[MetricsBase]

    @field_validator("metrics")
    @classmethod
    def validate_metrics(cls, metrics: list[MetricsBase]) -> list[MetricsBase]:
        """Verify that metrics met QC conditions."""
        failed_metrics = []
        for metric in metrics:
            if metric.condition is not None:
                qc_function: Callable = getattr(operator, metric.condition.norm)
                if not qc_function(metric.value, metric.condition.threshold):
                    metric_value = (
                        round(metric.value, PRECISION)
                        if isinstance(metric.value, float)
                        else metric.value
                    )
                    failed_metrics.append(
                        f"{metric.id} - {metric.name}={metric_value} (threshold: {metric.condition.norm} {metric.condition.threshold})"
                    )
        if failed_metrics:
            raise MetricsQCError(f"QC failed: {'; '.join(failed_metrics)}")
        return metrics


class MultiqcDataJson(BaseModel):
    """Multiqc data json model."""

    report_general_stats_data: list[dict] | None = None
    report_data_sources: dict | None = None
    report_saved_raw_data: dict[str, dict] | None = None
