from pydantic import BaseModel, Field


class PoolsRequest(BaseModel):
    enquiry: str | None = None
    page: int = 1
    page_size: int = Field(50, alias="pageSize")
