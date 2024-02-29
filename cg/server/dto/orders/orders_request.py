from pydantic import BaseModel, Field


class OrdersRequest(BaseModel):
    page_size: int | None = Field(alias="pageSize", default=50)
    page: int | None = 1
    workflow: str | None = None
    include_summary: bool = Field(default=False, alias="includeSummary")
