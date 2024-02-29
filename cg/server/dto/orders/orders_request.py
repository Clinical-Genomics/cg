from pydantic import BaseModel, Field


class OrdersRequest(BaseModel):
    page_size: int | None = Field(alias="pageSize", default=50)
    page: int | None = 1
    sort_field: str | None = Field(alias="sortField", default="order_date")
    sort_order: str | None = Field(alias="sortOrder", default="desc")
    workflow: str | None = None
    include_summary: bool = Field(default=False, alias="includeSummary")
