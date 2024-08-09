from pydantic import BaseModel


class SamplesRequest(BaseModel):
    status: str | None = None
    enquiry: str | None = None
    limit: int = 50
