from pydantic import BaseModel


class StatusSummary(BaseModel):
    count: int = 0
    case_ids: list[str] = []


class AnalysisSummary(BaseModel):
    order_id: int
    cancelled: StatusSummary
    completed: StatusSummary
    delivered: StatusSummary
    failed: StatusSummary
    running: StatusSummary

    @property
    def case_ids(self) -> list[str]:
        cancelled_case_ids: list[str] = self.cancelled.case_ids
        completed_case_ids: list[str] = self.completed.case_ids
        delivered_case_ids: list[str] = self.delivered.case_ids
        failed_case_ids: list[str] = self.failed.case_ids
        running_case_ids: list[str] = self.running.case_ids
        return (
            cancelled_case_ids
            + completed_case_ids
            + delivered_case_ids
            + failed_case_ids
            + running_case_ids
        )


class SummariesResponse(BaseModel):
    summaries: list[AnalysisSummary]
