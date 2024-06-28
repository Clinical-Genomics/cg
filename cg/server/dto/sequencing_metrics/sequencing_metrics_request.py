"""DTO for the sequencing metrics."""

from pydantic import BaseModel


class SequencingMetricsRequest(BaseModel):
    flow_cell_name: str
    flow_cell_lane_number: int
    sample_internal_id: str
    sample_total_reads_in_lane: int
    sample_base_percentage_passing_q30: float
