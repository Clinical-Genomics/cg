from pydantic import BaseModel, Field

from cg.models.orders.constants import OrderType


class CollaboratorSamplesRequest(BaseModel):
    customer: str
    enquiry: str
    limit: int = 50
    order_type: OrderType | None = None


class SamplesRequest(BaseModel):
    status: str | None = None
    enquiry: str | None = None
    page: int = 1
    page_size: int | None = Field(50, alias="pageSize")
