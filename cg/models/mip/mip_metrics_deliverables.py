from typing import Any, List, Optional

from pydantic import validator

from cg.constants.gender import Gender
from cg.models.deliverables.metric_deliverables import (
    SampleMetric,
    MeanInsertSize,
    MedianTargetCoverage,
    ParsedMetrics,
    MetricsDeliverables,
)

SAMPLE_METRICS_TO_PARSE: list = [
    "duplicate_reads",
    "mapped_reads",
    "mean_insert_size",
    "median_target_coverage",
    "predicted_sex",
]


def _get_metric_per_sample_id(sample_id: str, metric_objs: list) -> Any:
    """Get metric for a sample_id from metric object"""
    for metric in metric_objs:
        if sample_id == metric.sample_id:
            return metric


class DuplicateReads(SampleMetric):
    """Definition of duplicate reads metric"""

    value: float

    @validator("value", always=True)
    def convert_duplicate_read(cls, value) -> float:
        """Convert raw value from fraction to percent"""
        return value * 100


class GenderCheck(SampleMetric):
    """Definition of gender check metric"""

    value: str


class MIPMappedReads(SampleMetric):
    """Definition of mapped reads metric"""

    value: float

    @validator("value", always=True)
    def convert_mapped_read(cls, value) -> float:
        """Convert raw value from fraction to percent"""
        return value * 100


class MeanInsertSize(SampleMetric):
    """Definition of insert size metric"""

    value: float

    @validator("value", always=True)
    def convert_mean_insert_size(cls, value) -> int:
        """Convert raw value from float to int"""
        return int(value)


class MIPParsedMetrics(ParsedMetrics):
    """Defines parsed metrics"""

    duplicate_reads: float
    duplicate_reads_step: str
    mapped_reads: float
    mapped_reads_step: str
    predicted_sex: str = Gender.UNKNOWN
    predicted_sex_step: str


class MIPMetricsDeliverables(MetricsDeliverables):
    """Specification for a metric MIP deliverables file"""

    duplicate_reads: Optional[List[DuplicateReads]]
    mapped_reads: Optional[List[MIPMappedReads]]
    predicted_sex: Optional[List[GenderCheck]]
    sample_metric_to_parse: list = SAMPLE_METRICS_TO_PARSE
    sample_id_metrics: Optional[List[MIPParsedMetrics]]

    @validator("duplicate_reads", always=True)
    def set_duplicate_reads(cls, _, values: dict) -> List[DuplicateReads]:
        """Set duplicate_reads"""
        duplicate_reads: list = []
        raw_metrics: list = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "fraction_duplicates":
                duplicate_reads.append(
                    DuplicateReads(sample_id=metric.id, step=metric.step, value=metric.value)
                )
        return duplicate_reads

    @validator("mapped_reads", always=True)
    def set_mapped_reads(cls, _, values: dict) -> List[MIPMappedReads]:
        """Set mapped reads"""
        sample_ids: set = values.get("sample_ids")
        mapped_reads: list = []
        total_sequences: dict = {}
        reads_mapped: dict = {}
        raw_metrics: list = values.get("metrics_")
        metric_step: str = ""
        for metric in raw_metrics:
            if metric.name == "raw_total_sequences":
                raw_total_sequences = total_sequences.get(metric.id, 0)
                total_sequences[metric.id] = int(metric.value) + raw_total_sequences
                metric_step: str = metric.step
            if metric.name == "reads_mapped":
                raw_reads_mapped = reads_mapped.get(metric.id, 0)
                reads_mapped[metric.id] = int(metric.value) + raw_reads_mapped
        for sample_id in sample_ids:
            fraction_mapped_read = reads_mapped[sample_id] / total_sequences[sample_id]
            mapped_reads.append(
                MIPMappedReads(sample_id=sample_id, step=metric_step, value=fraction_mapped_read)
            )
        return mapped_reads

    @validator("mean_insert_size", always=True)
    def set_mean_insert_size(cls, _, values: dict) -> List[MeanInsertSize]:
        """Set mean insert size"""
        mean_insert_size: list = []
        raw_metrics: list = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "MEAN_INSERT_SIZE":
                mean_insert_size.append(
                    MeanInsertSize(sample_id=metric.id, step=metric.step, value=metric.value)
                )
        return mean_insert_size

    @validator("median_target_coverage", always=True)
    def set_median_target_coverage(cls, _, values: dict) -> List[MedianTargetCoverage]:
        """Set median target coverage"""
        median_target_coverage: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "MEDIAN_TARGET_COVERAGE":
                median_target_coverage.append(
                    MedianTargetCoverage(sample_id=metric.id, step=metric.step, value=metric.value)
                )
        return median_target_coverage

    @validator("predicted_sex", always=True)
    def set_predicted_sex(cls, _, values: dict) -> List[GenderCheck]:
        """Set predicted sex"""
        predicted_sex: list = []
        raw_metrics: list = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "gender":
                predicted_sex.append(
                    GenderCheck(sample_id=metric.id, step=metric.step, value=metric.value)
                )
        return predicted_sex

    @validator("sample_id_metrics", always=True)
    def set_sample_id_metrics(cls, _, values: dict) -> List[MIPParsedMetrics]:
        """Set parsed sample_id metrics gathered from all metrics"""
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
            sample_id_metrics.append(MIPParsedMetrics(**metric_per_sample_id))
        return sample_id_metrics


def get_sample_id_metric(
    sample_id_metrics: List[MIPParsedMetrics], sample_id: str
) -> MIPParsedMetrics:
    """Get parsed metrics for an sample_id"""
    for sample_id_metric in sample_id_metrics:
        if sample_id == sample_id_metric.sample_id:
            return sample_id_metric
