from pydantic import BaseModel


class AnalysisSummary(BaseModel):
    order_id: int
    cancelled: int
    completed: int
    delivered: int
    failed: int
    running: int


class SummariesResponse(BaseModel):
    summaries: list[AnalysisSummary]
