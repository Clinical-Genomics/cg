from datetime import datetime

from pydantic import BaseModel

from cg.clients.freshdesk.constants import Priority, Source, Status


class TicketCreate(BaseModel):
    """Freshdesk ticket."""

    attachments: list[dict[str, str]] = None
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


class TicketResponse(BaseModel):
    """Freshdesk ticket response."""

    attachments: list[dict[str, str]] = []
    created_at: datetime | None = None
    id: int
    priority: int
    source: int
    status: int
    subject: str
    tags: list[str] = []
    type: str | None = None
