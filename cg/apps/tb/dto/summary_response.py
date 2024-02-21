from pydantic import BaseModel


class Summary(BaseModel):
    order_id: int
    total: int
    delivered: int
    running: int
    cancelled: int
    failed: int


class SummariesResponse(BaseModel):
    summaries: list[Summary]
