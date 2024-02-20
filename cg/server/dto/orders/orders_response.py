from pydantic import BaseModel

from cg.constants import Workflow


class OrderSummary(BaseModel):
    total: int
    delivered: int | None = None
    running: int | None = None
    cancelled: int | None = None
    failed: int | None = None


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: str
    order_id: int
    workflow: Workflow
    summary: OrderSummary | None = None


class OrdersResponse(BaseModel):
    orders: list[Order]
