from pydantic import BaseModel


class DownsampleInput(BaseModel):
    sample_id: str
    case_name: str
    case_id: str
    number_of_reads: float
    account: str | None
    action: str | None
    ticket: str | None
    customer_id: str | None
    data_analysis: str | None
    data_delivery: str | None
