from pydantic import BaseModel


class CaseSummary(BaseModel):
    order_id: int
    not_received: int | None = None
    in_preparation: int | None = None
    in_sequencing: int | None = None
