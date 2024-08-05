from datetime import datetime

from pydantic import BaseModel

from cg.clients.freshdesk.constants import Priority, Source, Status


class TicketCreate(BaseModel):
    """Freshdesk ticket."""

    attachments: list[dict[str, str]] = []
    email: str
    email_config_id: int | None = None
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
    email: str
    id: int
    name: str | None = None
    priority: int
    source: int
    status: int
    subject: str
    tags: list[str] = []
    type: str | None = None
