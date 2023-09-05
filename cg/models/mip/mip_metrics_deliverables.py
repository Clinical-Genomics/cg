from typing import Any, Dict, List, Optional

from pydantic import BeforeValidator, FieldValidationInfo, field_validator
from typing_extensions import Annotated

from cg.constants.subject import Gender
from cg.models.balsamic.metrics import convert_to_percent
from cg.models.deliverables.metric_deliverables import (
    MeanInsertSize,
    MedianTargetCoverage,
    MetricsDeliverables,
    ParsedMetrics,
    SampleMetric,
    add_metric,
    add_sample_id_metrics,
)

SAMPLE_METRICS_TO_PARSE: List[str] = [
    "duplicate_reads",
    "mapped_reads",
    "mean_insert_size",
    "median_target_coverage",
    "predicted_sex",
]


class DuplicateReads(SampleMetric):
    """Definition of duplicate reads metric"""

    value: Annotated[float, BeforeValidator(convert_to_percent)]


class GenderCheck(SampleMetric):
    """Definition of gender check metric"""

    value: str


class MIPMappedReads(SampleMetric):
    """Definition of mapped reads metric"""

    value: Annotated[float, BeforeValidator(convert_to_percent)]


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

    metric_to_get_: Dict[str, Any] = {
        "fraction_duplicates": DuplicateReads,
        "MEAN_INSERT_SIZE": MeanInsertSize,
        "MEDIAN_TARGET_COVERAGE": MedianTargetCoverage,
        "gender": GenderCheck,
    }
    duplicate_reads: Optional[List[DuplicateReads]]
    mapped_reads: Optional[List[MIPMappedReads]]
    mean_insert_size: Optional[List[MeanInsertSize]]
    median_target_coverage: Optional[List[MedianTargetCoverage]]
    predicted_sex: Optional[List[GenderCheck]]
    sample_metric_to_parse: List[str] = SAMPLE_METRICS_TO_PARSE
    sample_id_metrics: Optional[List[MIPParsedMetrics]]

    @field_validator("duplicate_reads")
    @classmethod
    def set_duplicate_reads(cls, _, info: FieldValidationInfo) -> List[DuplicateReads]:
        """Set duplicate_reads"""
        return add_metric(name="fraction_duplicates", values=info.data)

    @field_validator("mapped_reads")
    @classmethod
    def set_mapped_reads(cls, _, info: FieldValidationInfo) -> List[MIPMappedReads]:
        """Set mapped reads"""
        sample_ids: set = info.data.get("sample_ids")
        mapped_reads: list = []
        total_sequences: dict = {}
        reads_mapped: dict = {}
        raw_metrics: list = info.data.get("metrics_")
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

    @field_validator("mean_insert_size")
    @classmethod
    def set_mean_insert_size(cls, _, info: FieldValidationInfo) -> List[MeanInsertSize]:
        """Set mean insert size"""
        return add_metric(name="MEAN_INSERT_SIZE", values=info.data)

    @field_validator("median_target_coverage")
    @classmethod
    def set_median_target_coverage(cls, _, info: FieldValidationInfo) -> List[MedianTargetCoverage]:
        """Set median target coverage"""
        return add_metric(name="MEDIAN_TARGET_COVERAGE", values=info.data)

    @field_validator("predicted_sex")
    @classmethod
    def set_predicted_sex(cls, _, info: FieldValidationInfo) -> List[GenderCheck]:
        """Set predicted sex"""
        return add_metric(name="gender", values=info.data)

    @field_validator("sample_id_metrics")
    @classmethod
    def set_sample_id_metrics(cls, _, info: FieldValidationInfo) -> List[MIPParsedMetrics]:
        """Set parsed sample_id metrics gathered from all metrics"""
        return add_sample_id_metrics(parsed_metric=MIPParsedMetrics, values=info.data)


def get_sample_id_metric(
    sample_id_metrics: List[MIPParsedMetrics], sample_id: str
) -> MIPParsedMetrics:
    """Get parsed metrics for an sample_id"""
    for sample_id_metric in sample_id_metrics:
        if sample_id == sample_id_metric.sample_id:
            return sample_id_metric
