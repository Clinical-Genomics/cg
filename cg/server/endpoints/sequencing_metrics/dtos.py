from pydantic import BaseModel

from cg.services.sample_run_metrics_service.dtos import PacbioSequencingMetricsDTO


class PacbioSequencingMetricsRequest(BaseModel):
    sample_id: str | None = None
    smrt_cell_ids: list[str] | None = None


class PacbioSequencingMetricsResponse(BaseModel):
    metrics: list[PacbioSequencingMetricsDTO] = []
