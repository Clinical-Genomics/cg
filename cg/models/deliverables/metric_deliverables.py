from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


def _get_metric_per_sample_id(sample_id: str, metric_objs: list) -> Any:
    """Get metric for a sample_id from metric object"""
    for metric in metric_objs:
        if sample_id == metric.sample_id:
            return metric


def add_metric(name: str, values: dict) -> List[Any]:
    """Add metric to list of objects"""
    found_metrics: list = []
    raw_metrics: list = values.get("metrics_")
    metrics_validator: Dict[str, Any] = values.get("metric_to_get_")
    for metric in raw_metrics:
        if name == metric.name and metric.name in metrics_validator:
            found_metrics.append(
                metrics_validator[metric.name](
                    sample_id=metric.id, step=metric.step, value=metric.value
                )
            )
    return found_metrics


def add_sample_id_metrics(parsed_metric: Any, values: dict) -> List[Any]:
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


class MetricsBase(BaseModel):
    """Definition for elements in deliverables metrics file"""

    header: Optional[str]
    id: str
    input: str
    name: str
    step: str
    value: Any


class SampleMetric(BaseModel):
    """Define base attribute for sample metrics"""

    sample_id: str
    step: str


class MeanInsertSize(SampleMetric):
    """Definition of insert size metric"""

    value: float

    @validator("value", always=True)
    def convert_mean_insert_size(cls, value) -> int:
        """Convert raw value from float to int"""
        return int(value)


class MedianTargetCoverage(SampleMetric):
    """Definition of median target coverage"""

    value: int


class ParsedMetrics(BaseModel):
    """Defines parsed metrics"""

    sample_id: str
    mean_insert_size: int
    mean_insert_size_step: str
    median_target_coverage: int
    median_target_coverage_step: str


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics_: List[MetricsBase] = Field(..., alias="metrics")
    sample_ids: Optional[set]

    @validator("sample_ids", always=True)
    def set_sample_ids(cls, _, values: dict) -> set:
        """Set sample_ids gathered from all metrics"""
        sample_ids: list = []
        raw_metrics: list = values.get("metrics_")
        for metric in raw_metrics:
            sample_ids.append(metric.id)
        return set(sample_ids)
