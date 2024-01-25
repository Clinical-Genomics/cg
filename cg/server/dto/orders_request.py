from pydantic import BaseModel

from cg.store.models import Order


class OrdersRequest(BaseModel):
    limit: int | None = None


class OrdersResponse(BaseModel):
    orders: list[Order]
