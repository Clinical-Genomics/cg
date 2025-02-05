from pydantic import BaseModel

from cg.services.sample_run_metrics_service.dtos import PacbioSequencingMetrics


class PacbioSequencingMetricsRequest(BaseModel):
    sample_id: str | None = None
    smrt_cell_id: str | None = None


class PacbioSequencingMetricsResponse(BaseModel):
    metrics: list[PacbioSequencingMetrics] = []
