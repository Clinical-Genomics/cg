from pydantic import BaseModel, Field


class OrderSummary(BaseModel):
    order_id: int = Field(exclude=True)
    total: int
    cancelled: int | None = None
    completed: int | None = None
    delivered: int | None = None
    failed: int | None = None
    in_lab_preparation: int | None = None
    in_sequencing: int | None = None
    not_received: int | None = None
    running: int | None = None
