from datetime import datetime

from pydantic import BaseModel


class PacbioSequencingRunDTO(BaseModel):
    barcoded_hifi_mean_read_length: int
    barcoded_hifi_reads: int
    barcoded_hifi_reads_percentage: float
    completed_at: datetime
    hifi_mean_read_length: int
    hifi_median_read_quality: str
    hifi_reads: int
    hifi_yield: int
    internal_id: str
    movie_name: str
    p0_percent: float
    p1_percent: float
    p2_percent: float
    percent_reads_passing_q30: float
    plate: int
    run_name: str
    started_at: datetime
    well: str


class PacbioSequencingRunsResponse(BaseModel):
    runs: list[PacbioSequencingRunDTO]
