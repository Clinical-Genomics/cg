from enum import StrEnum
from pydantic import BaseModel, Field


class SortField(StrEnum):
    ORDER_DATE: str = "order_date"
    ID: str = "id"
    CUSTOMER_ID: str = "customer_id"


class SortOrder(StrEnum):
    ASC: str = "asc"
    DESC: str = "desc"


class OrdersRequest(BaseModel):
    page_size: int | None = Field(alias="pageSize", default=50)
    page: int | None = 1
    sort_field: SortField | None = Field(alias="sortField", default=SortField.ORDER_DATE)
    sort_order: SortOrder | None = Field(alias="sortOrder", default=SortOrder.DESC)
    workflow: str | None = None
    include_summary: bool = Field(default=False, alias="includeSummary")
