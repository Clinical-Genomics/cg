from pydantic import BaseModel


class CaseStatusSummary(BaseModel):
    order_id: int
    in_sequencing: int
    in_preparation: int
