from typing import List, Optional, Any

from pydantic import BaseModel, validator, Field

from cg.constants.gender import Gender


def _get_metric_per_sample_id(sample_id: str, metric_objs: list) -> Any:
    """Get metric for a sample_id from metric object"""
    for metric in metric_objs:
        if sample_id == metric.sample_id:
            return metric.value


class MetricsBase(BaseModel):
    """Definition for elements in deliverables metrics file"""

    header: Optional[str]
    id: str
    input: str
    name: str
    step: str
    value: Any


class DuplicateReads(BaseModel):
    """Definition of duplicate reads metric"""

    sample_id: str
    value: float

    @validator("value", always=True)
    def convert_duplicate_read(cls, value) -> float:
        """Convert raw value from fraction to percent"""
        return value * 100


class GenderCheck(BaseModel):
    """Definition of gender check metric"""

    sample_id: str
    value: str


class MappedReads(BaseModel):
    """Definition of mapped reads metric"""

    sample_id: str
    value: float

    @validator("value", always=True)
    def convert_mapped_read(cls, value) -> float:
        """Convert raw value from fraction to percent"""
        return value * 100


class MeanInsertSize(BaseModel):
    """Definition of insert size metric"""

    sample_id: str
    value: float

    @validator("value", always=True)
    def convert_mean_insert_size(cls, value) -> int:
        """Convert raw value from float to int"""
        return int(value)


class ParsedMetrics(BaseModel):
    """Defines parsed metrics"""

    sample_id: str
    duplicate_reads: float
    mapped_reads: float
    mean_insert_size: int
    predicted_sex: str = Gender.UNKNOWN


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics_: List[MetricsBase] = Field(..., alias="metrics")
    sample_ids: Optional[set]
    duplicate_reads: Optional[List[DuplicateReads]]
    mapped_reads: Optional[List[MappedReads]]
    mean_insert_size: Optional[List[MeanInsertSize]]
    predicted_sex: Optional[List[GenderCheck]]
    sample_id_metrics: Optional[List[ParsedMetrics]]

    @validator("sample_ids", always=True)
    def set_sample_ids(cls, _, values: dict) -> set:
        """Set sample_ids gathered from all metrics"""
        sample_ids: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            sample_ids.append(metric.id)
        return set(sample_ids)

    @validator("duplicate_reads", always=True)
    def set_duplicate_reads(cls, _, values: dict) -> List[DuplicateReads]:
        """Set duplicate_reads"""
        duplicate_reads: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "fraction_duplicates":
                duplicate_reads.append(DuplicateReads(sample_id=metric.id, value=metric.value))
        return duplicate_reads

    @validator("mapped_reads", always=True)
    def set_mapped_reads(cls, _, values: dict) -> List[MappedReads]:
        """Set mapped reads"""
        sample_ids: set = values.get("sample_ids")
        mapped_reads: List = []
        total_sequences: dict = {}
        reads_mapped: dict = {}
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "raw_total_sequences":
                raw_total_sequences = total_sequences.get(metric.id, 0)
                total_sequences[metric.id] = int(metric.value) + raw_total_sequences
            if metric.name == "reads_mapped":
                raw_reads_mapped = reads_mapped.get(metric.id, 0)
                reads_mapped[metric.id] = int(metric.value) + raw_reads_mapped
        for sample_id in sample_ids:
            fraction_mapped_read = reads_mapped[sample_id] / total_sequences[sample_id]
            mapped_reads.append(MappedReads(sample_id=sample_id, value=fraction_mapped_read))
        return mapped_reads

    @validator("mean_insert_size", always=True)
    def set_mean_insert_size(cls, _, values: dict) -> List[MeanInsertSize]:
        """Set mean insert size"""
        mean_insert_size: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "MEAN_INSERT_SIZE":
                mean_insert_size.append(MeanInsertSize(sample_id=metric.id, value=metric.value))
        return mean_insert_size

    @validator("predicted_sex", always=True)
    def set_predicted_sex(cls, _, values: dict) -> List[GenderCheck]:
        """Set predicted sex"""
        predicted_sex: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name == "gender":
                predicted_sex.append(GenderCheck(sample_id=metric.id, value=metric.value))
        return predicted_sex

    @validator("sample_id_metrics", always=True)
    def set_sample_id_metrics(cls, _, values: dict) -> List[ParsedMetrics]:
        """Set parsed sample_id metrics gathered from all metrics"""
        sample_ids: set = values.get("sample_ids")
        sample_id_metrics: list = []
        metric_per_sample_id_map: dict = {
            "duplicate_reads": values.get("duplicate_reads"),
            "mapped_reads": values.get("mapped_reads"),
            "mean_insert_size": values.get("mean_insert_size"),
            "predicted_sex": values.get("predicted_sex"),
        }
        for sample_id in sample_ids:
            metric_per_sample_id: dict = {}
            metric_per_sample_id["sample_id"] = sample_id
            for metric_name, metric_objs in metric_per_sample_id_map.items():
                metric_value: Any = _get_metric_per_sample_id(
                    sample_id=sample_id, metric_objs=metric_objs
                )
                if metric_value:
                    metric_per_sample_id[metric_name] = metric_value
            sample_id_metrics.append(ParsedMetrics(**metric_per_sample_id))
        return sample_id_metrics


def get_sample_id_metric(sample_id_metrics: List[ParsedMetrics], sample_id: str) -> ParsedMetrics:
    """Get parsed metrics for an sample_id"""
    for sample_id_metric in sample_id_metrics:
        if sample_id == sample_id_metric.sample_id:
            return sample_id_metric
