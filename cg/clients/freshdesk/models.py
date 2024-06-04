from datetime import datetime

from pydantic import BaseModel


class Ticket(BaseModel):
    attachments: list[dict[str, str]] | None = None
    cc_emails: list[str] | None = None
    company_id: int | None = None
    custom_fields: dict | None = None
    description: str | None = None
    due_by: datetime | None = None
    email: str | None = None
    email_config_id: int | None = None
    facebook_id: str | None = None
    fr_due_by: datetime | None = None
    group_id: int | None = None
    id: int | None = None
    name: str | None = None
    phone: str | None = None
    priority: int = 1
    product_id: int | None = None
    requester_id: int | None = None
    responder_id: int | None = None
    source: int = 2
    status: int = 3
    subject: str = ""
    tags: list[str] | None = None
    twitter_id: str | None = None
    type: str | None = None


class TicketResponse(BaseModel):
    cc_emails: list[str]
    fwd_emails: list[str]
    reply_cc_emails: list[str]
    email_config_id: int | None
    group_id: int | None
    priority: int
    requester_id: int
    responder_id: int | None
    source: int
    status: int
    subject: str
    company_id: int | None = None
    id: int
    type: str | None = None
    to_emails: list[str] | None = []
    product_id: int | None
    fr_escalated: bool
    spam: bool
    urgent: bool = False
    is_escalated: bool
    created_at: datetime
    updated_at: datetime
    due_by: datetime
    fr_due_by: datetime
    description_text: str
    description: str
    custom_fields: dict = {}
    tags: list[str]
    attachments: list[dict[str, str]]


class Reply(BaseModel):
    body: str
    attachments: list[dict] = []
    from_email: str = None
    user_id: int = None
    cc_emails: list[str] = []
    bcc_emails: list[str] = []


class ReplyResponse(BaseModel):
    body_text: str
    body: str
    id: int
    user_id: int
    from_email: str
    cc_emails: list[str]
    bcc_emails: list[str]
    ticket_id: int
    attachments: list[dict]
    created_at: datetime
    updated_at: datetime
