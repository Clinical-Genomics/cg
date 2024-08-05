from enum import StrEnum
from pydantic import BaseModel, Field


class OrderSortField(StrEnum):
    ORDER_DATE: str = "order_date"
    ID: str = "id"
    CUSTOMER_ID: str = "customer_id"


class SortOrder(StrEnum):
    ASC: str = "asc"
    DESC: str = "desc"


class OrdersRequest(BaseModel):
    page_size: int | None = Field(alias="pageSize", default=50)
    page: int | None = 1
    sort_field: OrderSortField | None = Field(alias="sortField", default=OrderSortField.ORDER_DATE)
    sort_order: SortOrder | None = Field(alias="sortOrder", default=SortOrder.DESC)
    search: str | None = None
    workflow: str | None = None
    delivered: bool | None = None
