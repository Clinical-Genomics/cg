from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class StatsSample(BaseModel):
    name: str
    reads: int = 0
    fastqs: List[str] = []


class StatsFlowcell(BaseModel):
    name: str
    sequencer: Optional[str]
    sequencer_type: str
    date: datetime
    samples: List[StatsSample]
