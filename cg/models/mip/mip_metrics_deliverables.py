from typing import List, Optional

from pydantic import BaseModel


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
