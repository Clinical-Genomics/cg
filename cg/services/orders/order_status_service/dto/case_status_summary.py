from pydantic import BaseModel


class CaseSummary(BaseModel):
    order_id: int
    in_sequencing: int
    in_lab_preparation: int
