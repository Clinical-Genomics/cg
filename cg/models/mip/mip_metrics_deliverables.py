from typing import List, Optional, Any, Dict

from pydantic import BaseModel, validator


class MetricsBase(BaseModel):
    """Definition for elements in deliverables metrics file"""

    header: Optional[str]
    id: str
    input: str
    name: str
    step: str
    value: str


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics: List[MetricsBase]
    duplicates: Optional[Dict]

    @validator("duplicates", always=True)
    def set_duplicates(cls, _, values: dict) -> dict:
        """Set duplicates"""
        duplicate: dict = {}
        raw_metrics: List = values.get("metrics")
        for metric in raw_metrics:
            if metric.step is "markduplicates":
                duplicate[metric.id] = float(metric.value)
        return duplicate
