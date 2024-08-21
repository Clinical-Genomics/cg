from typing import List, Tuple, Union, Dict, Optional
from pydantic import BaseModel, Field

from cg.clients.freshdesk.constants import Priority, Source, Status


class TicketCreate(BaseModel):
    """Freshdesk ticket."""

    attachments: List[Union[str, bytes]] = Field(default_factory=list)
    email_config_id: int | None = None
    description: str
    name: str
    priority: int = Priority.LOW
    source: int = Source.EMAIL
    status: int = Status.OPEN
    subject: str
    tags: list[str] = []
    type: str | None = None
    custom_fields: Dict[str, Union[str, int, float, None]] = Field(default_factory=dict)

    def to_multipart_data(self) -> List[Tuple[str, Union[str, int, bytes]]]:
        """Convert the TicketCreate model into a list of tuples for multipart form data required by the Freshdesk API."""
        multipart_data = []

        for field, value in self.model_dump(exclude_none=True).items():
            if isinstance(value, list) and field == "tags":
                multipart_data.extend([("tags[]", tag) for tag in value])
            elif isinstance(value, dict) and field == "custom_fields":
                multipart_data.extend(
                    [(f"custom_fields[{key}]", val) for key, val in value.items()]
                )
            else:
                multipart_data.append((field, value))

        return multipart_data


class TicketResponse(BaseModel):

    id: int
    description: str
    subject: str
    to_emails: Optional[List[str]] = None
    status: int
    priority: int
