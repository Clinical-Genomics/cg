from pydantic import BaseModel


class PacbioSequencingMetricsRequest(BaseModel):
    sample_id: str | None = None
    smrt_cell_id: str | None = None
