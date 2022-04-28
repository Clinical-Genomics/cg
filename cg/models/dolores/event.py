from datetime import datetime
from typing import Optional


from pydantic import BaseModel, AnyUrl


class Event(BaseModel):
    created_at: Optional[datetime]
    creator_id: Optional[str]
    event_name: str


class EventUpload(Event):
    uploaded_at: datetime
    uploaded_to: str
    uploaded_to_url: Optional[AnyUrl]


class EventComment(Event):
    content: str
