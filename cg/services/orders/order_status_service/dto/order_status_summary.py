from pydantic import BaseModel


class OrderStatusSummary(BaseModel):
    order_id: int
    total: int
    delivered: int | None = None
    running: int | None = None
    cancelled: int | None = None
    failed: int | None = None
