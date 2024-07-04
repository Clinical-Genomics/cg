from pydantic import BaseModel, Field

from cg.apps.tb.dto.summary_response import StatusSummary


class OrderSummary(BaseModel):
    order_id: int = Field(exclude=True)
    total: int
    cancelled: StatusSummary
    completed: StatusSummary
    delivered: StatusSummary
    failed: StatusSummary
    failed_sequencing_qc: StatusSummary
    in_lab_preparation: StatusSummary
    in_sequencing: StatusSummary
    not_received: StatusSummary
    running: StatusSummary
