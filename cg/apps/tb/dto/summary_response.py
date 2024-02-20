from pydantic import BaseModel


class Summary(BaseModel):
    order_id: int
    total: int
    delivered: int | None = None
    running: int | None = None
    cancelled: int | None = None
    failed: int | None = None


class SummariesResponse(BaseModel):
    summaries: list[Summary]
