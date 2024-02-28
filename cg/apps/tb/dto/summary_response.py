from pydantic import BaseModel


class AnalysisSummary(BaseModel):
    order_id: int
    delivered: int | None = None
    running: int | None = None
    cancelled: int | None = None
    failed: int | None = None


class SummariesResponse(BaseModel):
    summaries: list[AnalysisSummary]
