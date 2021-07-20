from enum import Enum
from typing import List, Optional, Any

from pydantic import BaseModel, validator


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
    value: str


class DuplicateReads(BaseModel):
    """Definition of duplicate reads metric"""

    value: float
    id: str


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class GenderCheck(BaseModel):
    """Definition of gender check metric"""

    value: str
    id: str


class ParsedMetrics(BaseModel):
    """Defines parsed metrics"""

    id: str
    duplicate_reads: float
    predicted_sex: Gender = Gender.UNKNOWN


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics: List[MetricsBase]
    ids: Optional[set]
    duplicate_reads: Optional[List[DuplicateReads]]
    predicted_sex: Optional[List[GenderCheck]]
    id_metrics: Optional[List[ParsedMetrics]]

    @validator("ids", always=True)
    def set_ids(cls, _, values: dict) -> set:
        """Set ids gathered from all metrics"""
        ids: List = []
        raw_metrics: List = values.get("metrics")
        for metric in raw_metrics:
            ids.append(metric.id)
        return set(ids)

    @validator("duplicate_reads", always=True)
    def set_duplicate_reads(cls, _, values: dict) -> List[DuplicateReads]:
        """Set duplicate_reads"""
        duplicate_reads: List = []
        raw_metrics: List = values.get("metrics")
        for metric in raw_metrics:
            if metric.name is "fraction_duplicates":
                duplicate_reads.append(DuplicateReads(id=metric.id, value=float(metric.value)))
        return duplicate_reads

    @validator("predicted_sex", always=True)
    def set_predicted_sex(cls, _, values: dict) -> List[GenderCheck]:
        """Set predicted sex"""
        predicted_sex: List = []
        raw_metrics: List = values.get("metrics")
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
