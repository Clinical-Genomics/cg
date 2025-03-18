from datetime import date
from typing import Tuple, Union

from pydantic import BaseModel, EmailStr, Field

from cg.clients.freshdesk.constants import Priority, Source, Status


class TicketCreate(BaseModel):
    """Freshdesk ticket."""

    attachments: list[str | bytes] = Field(default_factory=list)
    email: EmailStr
    email_config_id: int | None = None
    description: str
    name: str
    priority: int = Priority.LOW
    source: int = Source.EMAIL
    status: int = Status.PENDING
    due_by: date
    fr_due_by: date
    subject: str
    tags: list[str] = []
    type: str | None = None
    custom_fields: dict[str, str | int | float | None] = Field(default_factory=dict)

    def to_multipart_data(self) -> list[Tuple[str, str | int | bytes]]:
        """Custom converter to multipart form data."""
        multipart_data = []

        for field, value in self.model_dump(exclude_none=True).items():
            if isinstance(value, list):
                multipart_data.extend([(f"{field}[]", v) for v in value])
            elif isinstance(value, dict):
                multipart_data.extend([(f"{field}[{k}]", v) for k, v in value.items()])
            else:
                multipart_data.append((field, value))

        return multipart_data


class TicketResponse(BaseModel):
    """Response from Freshdesk"""

    id: int
    description: str
    subject: str
    to_emails: list[str] | None = None
    status: int
    priority: int


class ReplyCreate(BaseModel):
    """Reply to a ticket."""

    ticket_number: str
    body: str

    def to_multipart_data(self) -> list[Tuple[str, Union[str, int, bytes]]]:
        """Custom converter to multipart form data."""
        multipart_data = [
            ("body", self.body),
        ]
        return multipart_data
