from datetime import datetime

from pydantic import BaseModel


class Ticket(BaseModel):
    """Freshdesk ticket."""

    association_type: int | None = None
    attachments: list[dict[str, str]] = []
    cc_emails: list[str] = []
    company_id: int | None = None
    custom_fields: dict | None = None
    deleted: bool | None = None
    description: str | None = None
    description_text: str | None = None
    due_by: datetime | None = None
    email: str | None = None
    email_config_id: int | None = None
    facebook_id: str | None = None
    fr_due_by: datetime | None = None
    fr_escalated: bool | None = None
    fwd_emails: list[str] = []
    group_id: int | None = None
    id: int | None = None
    is_escalated: bool | None = None
    name: str | None = None
    phone: str | None = None
    priority: int = 1
    product_id: int | None = None
    reply_cc_emails: list[str] = []
    requester_id: int | None = None
    responder_id: int | None = None
    source: int = 2
    source_additional_info: str | None = None
    spam: bool | None = None
    status: int = 3
    subject: str = ""
    tags: list[str] = []
    to_emails: list[str] = []
    twitter_id: str | None = None
    type: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
