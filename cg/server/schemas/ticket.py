from pydantic import BaseModel, EmailStr


class TicketIn(BaseModel):
    name: str
    email: EmailStr
