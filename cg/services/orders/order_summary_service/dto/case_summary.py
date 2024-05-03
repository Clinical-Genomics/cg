from pydantic import BaseModel


class CaseSummary(BaseModel):
    order_id: int
    failed_sequencing_qc: int | None = None
    in_preparation: int | None = None
    in_sequencing: int | None = None
    not_received: int | None = None
