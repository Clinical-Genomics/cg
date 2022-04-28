from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from cg.models.dolores.event import EventUpload


class Analysis(BaseModel):
    cleaned_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: Optional[datetime]
    is_primary: bool
    pipeline_version: str
    started_at: Optional[datetime]
    upload_events: Optional[List[EventUpload]]
