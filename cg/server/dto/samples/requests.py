from pydantic import BaseModel, Field


class CollaboratorSamplesRequest(BaseModel):
    enquiry: str
    customer: str
    limit: int = 50


class SamplesRequest(BaseModel):
    status: str | None = None
    enquiry: str | None = None
    page: int = 1
    page_size: int | None = Field(50, alias="pageSize")
