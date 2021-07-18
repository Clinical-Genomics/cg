from typing import List, Optional

from pydantic import BaseModel, validator


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
    sample_id: str


class MetricsDeliverables(BaseModel):
    """Specification for a metric general deliverables file"""

    metrics: List[MetricsBase]
    duplicate_reads: Optional[List[DuplicateReads]]

    @validator("duplicate_reads", always=True)
    def set_duplicate_reads(cls, _, values: dict) -> List[DuplicateReads]:
        """Set duplicate_reads"""
        duplicate_reads: List = []
        raw_metrics: List = values.get("metrics")
        for metric in raw_metrics:
            if metric.step is "markduplicates":
                duplicate_reads.append(
                    DuplicateReads(sample_id=metric.id, value=float(metric.value))
                )
        return duplicate_reads
