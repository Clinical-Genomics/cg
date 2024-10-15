from typing import Annotated, Any

from pydantic import Field, ValidationInfo, field_validator

from cg.constants.subject import Sex
from cg.models.deliverables.metric_deliverables import (
    MeanInsertSize,
    MedianTargetCoverage,
    MetricsDeliverables,
    ParsedMetrics,
    SampleMetric,
    add_metric,
    add_sample_id_metrics,
)

SAMPLE_METRICS_TO_PARSE: list[str] = [
    "duplicate_reads",
    "mapped_reads",
    "mean_insert_size",
    "median_target_coverage",
    "predicted_sex",
]


class DuplicateReads(SampleMetric):
    """Definition of duplicate reads metric"""

    value: float

    @field_validator("value")
    @classmethod
    def convert_duplicate_read(cls, value) -> float:
        """Convert raw value from fraction to percent."""
        return value * 100


class SexCheck(SampleMetric):
    """Definition of sex check metric."""

    value: str


class MIPMappedReads(SampleMetric):
    """Definition of mapped reads metric"""

    value: float

    @field_validator("value")
    @classmethod
    def convert_mapped_read(cls, value) -> float:
        """Convert raw value from fraction to percent"""
        return value * 100


class MIPParsedMetrics(ParsedMetrics):
    """Defines parsed metrics"""

    duplicate_reads: float
    duplicate_reads_step: str
    mapped_reads: float
    mapped_reads_step: str
    predicted_sex: str = Sex.UNKNOWN
    predicted_sex_step: str


class MIPMetricsDeliverables(MetricsDeliverables):
    """Specification for a metric MIP deliverables file"""

    metric_to_get_: dict[str, Any] = {
        "fraction_duplicates": DuplicateReads,
        "MEAN_INSERT_SIZE": MeanInsertSize,
        "MEDIAN_TARGET_COVERAGE": MedianTargetCoverage,
        "gender": SexCheck,
    }
    duplicate_reads: Annotated[list[DuplicateReads] | None, Field(validate_default=True)] = None
    mapped_reads: Annotated[list[MIPMappedReads] | None, Field(validate_default=True)] = None
    mean_insert_size: Annotated[list[MeanInsertSize] | None, Field(validate_default=True)] = None
    median_target_coverage: Annotated[
        list[MedianTargetCoverage] | None, Field(validate_default=True)
    ] = None
    predicted_sex: Annotated[list[SexCheck] | None, Field(validate_default=True)] = None
    sample_metric_to_parse: list[str] = SAMPLE_METRICS_TO_PARSE
    sample_id_metrics: Annotated[list[MIPParsedMetrics] | None, Field(validate_default=True)] = None

    @field_validator("duplicate_reads")
    @classmethod
    def set_duplicate_reads(cls, _, info: ValidationInfo) -> list[DuplicateReads]:
        """Set duplicate_reads"""
        return add_metric(name="fraction_duplicates", info=info)

    @field_validator("mapped_reads")
    @classmethod
    def set_mapped_reads(cls, _, info: ValidationInfo) -> list[MIPMappedReads]:
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
            elif metric.name == "reads_mapped":
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
    def set_mean_insert_size(cls, _, info: ValidationInfo) -> list[MeanInsertSize]:
        """Set mean insert size"""
        return add_metric(name="MEAN_INSERT_SIZE", info=info)

    @field_validator("median_target_coverage")
    @classmethod
    def set_median_target_coverage(cls, _, info: ValidationInfo) -> list[MedianTargetCoverage]:
        """Set median target coverage"""
        return add_metric(name="MEDIAN_TARGET_COVERAGE", info=info)

    @field_validator("predicted_sex")
    @classmethod
    def set_predicted_sex(cls, _, info: ValidationInfo) -> list[SexCheck]:
        """Set predicted sex"""
        return add_metric(name="gender", info=info)

    @field_validator("sample_id_metrics")
    @classmethod
    def set_sample_id_metrics(cls, _, info: ValidationInfo) -> list[MIPParsedMetrics]:
        """Set parsed sample_id metrics gathered from all metrics"""
        return add_sample_id_metrics(parsed_metric=MIPParsedMetrics, info=info)


def get_sample_id_metric(
    sample_id_metrics: list[MIPParsedMetrics], sample_id: str
) -> MIPParsedMetrics:
    """Get parsed metrics for a sample id"""
    for sample_id_metric in sample_id_metrics:
        if sample_id == sample_id_metric.sample_id:
            return sample_id_metric
    raise ValueError(f"Could not find metric for: {sample_id}")
