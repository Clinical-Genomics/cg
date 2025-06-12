from pydantic import BaseModel


class IlluminaSequencingMetricsDTO(BaseModel):
    flow_cell_name: str
    flow_cell_lane_number: int
    sample_internal_id: str
    sample_total_reads_in_lane: int
    sample_base_percentage_passing_q30: float


class PacbioSequencingMetricsDTO(BaseModel):
    hifi_mean_read_length: int
    hifi_median_read_quality: str
    hifi_reads: int
    hifi_yield: int
    sample_id: str
    smrt_cell_id: str
