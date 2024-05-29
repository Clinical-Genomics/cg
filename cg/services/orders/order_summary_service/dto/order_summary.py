from pydantic import BaseModel, Field


class OrderSummary(BaseModel):
    order_id: int = Field(exclude=True)
    total: int
    cancelled: int
    completed: int
    delivered: int
    failed: int
    failed_sequencing_qc: int
    in_lab_preparation: int
    in_sequencing: int
    not_received: int
    running: int
