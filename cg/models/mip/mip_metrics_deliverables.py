from typing import List, Optional, Any

from pydantic import BaseModel, validator, Field

from cg.constants.gender import Gender


def _get_id_metric(id: str, metric_objs: list) -> Any:
    """Get metric for an id from metric object"""
    for metric in metric_objs:
        if id == metric.id:
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

    id: str
    value: float


class GenderCheck(BaseModel):
    """Definition of gender check metric"""

    id: str
    value: str


class MappedReads(BaseModel):
    """Definition of mapped reads metric"""

    id: str
    value: float


class MeanInsertSize(BaseModel):
    """Definition of insert size metric"""

    id: str
    value: float

    @validator("value", always=True)
    def convert_mean_insert_size(cls, value) -> int:
        """Convert raw value from float to int"""
        return int(value)


class ParsedMetrics(BaseModel):
    """Defines parsed metrics"""

    id: str
    duplicate_reads: float
    mapped_reads: float
    mean_insert_size: int
    predicted_sex: Gender = Gender.UNKNOWN


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics_: List[MetricsBase] = Field(..., alias="metrics")
    ids: Optional[set]
    duplicate_reads: Optional[List[DuplicateReads]]
    mapped_reads: Optional[List[MappedReads]]
    mean_insert_size: Optional[List[MeanInsertSize]]
    predicted_sex: Optional[List[GenderCheck]]
    id_metrics: Optional[List[ParsedMetrics]]

    @validator("ids", always=True)
    def set_ids(cls, _, values: dict) -> set:
        """Set ids gathered from all metrics"""
        ids: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            ids.append(metric.id)
        return set(ids)

    @validator("duplicate_reads", always=True)
    def set_duplicate_reads(cls, _, values: dict) -> List[DuplicateReads]:
        """Set duplicate_reads"""
        duplicate_reads: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name is "fraction_duplicates":
                duplicate_reads.append(DuplicateReads(id=metric.id, value=metric.value))
        return duplicate_reads

    @validator("mapped_reads", always=True)
    def set_mapped_reads(cls, _, values: dict) -> List[MappedReads]:
        """Set mapped reads"""
        ids: set = values.get("ids")
        mapped_reads: List = []
        total_sequences: dict = {}
        reads_mapped: dict = {}
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name is "raw_total_sequences":
                raw_total_sequences = total_sequences.get(metric.id, 0)
                total_sequences[metric.id] = int(metric.value) + raw_total_sequences
            if metric.name is "reads_mapped":
                raw_reads_mapped = reads_mapped.get(metric.id, 0)
                reads_mapped[metric.id] = int(metric.value) + raw_reads_mapped
        for id in ids:
            fraction_mapped_read = reads_mapped[id] / total_sequences[id]
            mapped_reads.append(MappedReads(id=id, value=fraction_mapped_read))
        return mapped_reads

    @validator("mean_insert_size", always=True)
    def set_mean_insert_size(cls, _, values: dict) -> List[MeanInsertSize]:
        """Set mean insert size"""
        mean_insert_size: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name is "MEAN_INSERT_SIZE":
                mean_insert_size.append(MeanInsertSize(id=metric.id, value=metric.value))
        return mean_insert_size

    @validator("predicted_sex", always=True)
    def set_predicted_sex(cls, _, values: dict) -> List[GenderCheck]:
        """Set predicted sex"""
        predicted_sex: List = []
        raw_metrics: List = values.get("metrics_")
        for metric in raw_metrics:
            if metric.name is "gender":
                predicted_sex.append(GenderCheck(id=metric.id, value=metric.value))
        return predicted_sex

    @validator("id_metrics", always=True)
    def set_id_metrics(cls, _, values: dict) -> List[ParsedMetrics]:
        """Set parsed id metrics gathered from all metrics"""
        ids: set = values.get("ids")
        id_metrics: list = []
        metric_per_id_map: dict = {
            "duplicate_reads": values.get("duplicate_reads"),
            "mapped_reads": values.get("mapped_reads"),
            "mean_insert_size": values.get("mean_insert_size"),
            "predicted_sex": values.get("predicted_sex"),
        }
        for id in ids:
            metric_per_id: dict = {}
            metric_per_id["id"] = id
            for metric_name, metric_objs in metric_per_id_map.items():
                metric_value: Any = _get_id_metric(id=id, metric_objs=metric_objs)
                if metric_value:
                    metric_per_id[metric_name] = metric_value
                    continue
            id_metrics.append(ParsedMetrics(**metric_per_id))
        return id_metrics
