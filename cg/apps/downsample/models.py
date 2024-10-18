from pydantic import BaseModel


class DownsampleInput(BaseModel):
    sample_id: str
    case_name: str
    case_id: str
    number_of_reads: float
    account: str | None = None
    action: str | None = None
    ticket: str | None = None
    customer_id: str | None = None
    data_analysis: str | None = None
    data_delivery: str | None = None
