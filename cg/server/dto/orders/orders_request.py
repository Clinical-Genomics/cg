from pydantic import BaseModel, Field


class OrdersRequest(BaseModel):
    limit: int | None = None
    workflow: str | None = None
    include_summary: bool = Field(default=False, alias="includeSummary")
