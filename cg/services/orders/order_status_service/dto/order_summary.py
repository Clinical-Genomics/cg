from pydantic import BaseModel, Field


class OrderSummary(BaseModel):
    order_id: int = Field(exclude=True)
    total: int
    delivered: int | None = None
    running: int | None = None
    cancelled: int | None = None
    failed: int | None = None
    in_sequencing: int | None = None
    in_lab_preparation: int | None = None
    not_received: int | None = None
