from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Sequencing(BaseModel):
    application_id: str
    application_pricing_version: int
    prepared_at: Optional[datetime]
    sequenced_at: Optional[datetime]
    sequence_reads: int
