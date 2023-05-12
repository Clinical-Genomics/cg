from pydantic import BaseModel, Field, validator
from typing import List


class SequencingMetricsForLaneAndSample(BaseModel):
    """
    Contains the parsed bcl2fastq sequencing metrics output.
    The data is parsed per lane and sample and is validated.
    """

    flow_cell_name: str = Field(..., min_length=1)
    number_of_lanes: int = Field(..., gt=0)
    lane_number: int = Field(..., ge=0)
    sample_id: str = Field(..., min_length=1)

    yield_in_bases: int = Field(..., ge=0)
    passing_filter_clusters_count: int = Field(..., ge=0)
    raw_clusters_count: int = Field(..., ge=0)
    read_count: int = Field(..., gt=0)
    perfect_reads_for_sample: int = Field(..., gt=0)
    yield_values: List[int] = Field(min_items=0)
    q30_yield_values: List[int] = Field(min_items=0)
    quality_score_values: List[int] = Field(min_items=0)

    @validator("yield_values", "q30_yield_values", "quality_score_values", each_item=True)
    def check_non_negative(cls, value):
        if value < 0:
            raise ValueError("List values must be non-negative")
        return value
