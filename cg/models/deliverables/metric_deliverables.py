from typing import Any, List, Optional

from pydantic import BaseModel, Field, validator


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
    mean_insert_size: Optional[List[MeanInsertSize]]
    median_target_coverage: Optional[List[MedianTargetCoverage]]

    @validator("sample_ids", always=True)
    def set_sample_ids(cls, _, values: dict) -> set:
        """Set sample_ids gathered from all metrics"""
        sample_ids: list = []
        raw_metrics: list = values.get("metrics_")
        for metric in raw_metrics:
            sample_ids.append(metric.id)
        return set(sample_ids)
