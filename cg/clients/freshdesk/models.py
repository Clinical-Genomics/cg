from datetime import datetime
from typing import List, Union, Optional
from pydantic import BaseModel, Field

from cg.clients.freshdesk.constants import Priority, Source, Status


class TicketCreate(BaseModel):
    """Freshdesk ticket."""

    attachments: List[Union[str, bytes]] = Field(default_factory=list)
    email: str
    email_config_id: int | None = None
    description: str
    name: str
    priority: int = Priority.LOW
    source: int = Source.EMAIL
    status: int = Status.OPEN
    subject: str
    tags: list[str] = []
    type: str | None = None


class Attachment(BaseModel):
    id: int
    name: str
    content_type: str
    size: int
    created_at: str


class TicketResponse(BaseModel):
    id: int
    description: str
    subject: str
    to_emails: Optional[List[str]] = None
    status: int
    priority: int
    attachments: Optional[List[Attachment]] = None
