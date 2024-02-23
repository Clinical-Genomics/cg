from pydantic import BaseModel


class AnalysisSummary(BaseModel):
    order_id: int
    delivered: int
    running: int
    cancelled: int
    failed: int


class SummariesResponse(BaseModel):
    summaries: list[AnalysisSummary]
