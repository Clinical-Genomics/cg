from typing import List, Optional, Set

from pydantic import BaseModel, Field, validator


class Unaligned(BaseModel):
    lane: int
    read_count: int = Field(..., alias="readcounts")
    yield_mb: int
    passed_filter_pct: float

    q30_bases_pct: float
    mean_quality_score: float

    class Config:
        orm_mode = True


class StatsSample(BaseModel):
    sample_name: str = Field(..., alias="samplename")
    unaligned: List[Unaligned]
    lanes: List[int] = []
    read_count_sum: int = 0
    sum_yield: int = 0

    @validator("lanes", always=True)
    def set_lanes(cls, _, values: dict) -> List[int]:
        """Set the number of pass filter clusters"""
        unaligned_reads: List[Unaligned] = values["unaligned"]
        lanes_found: Set[int] = set()
        for read in unaligned_reads:
            lanes_found.add(read.lane)
        return list(lanes_found)

    @validator("read_count_sum", always=True)
    def set_read_count(cls, _, values: dict):
        unaligned_reads: List[Unaligned] = values["unaligned"]
        count: int = 0
        for read in unaligned_reads:
            count += read.read_count
        return count

    @validator("sum_yield", always=True)
    def set_sum_yield(cls, _, values: dict):
        unaligned_reads: List[Unaligned] = values["unaligned"]
        count: int = 0
        for read in unaligned_reads:
            count += read.yield_mb
        return count

    @validator("unaligned")
    def sort_unaligned(cls, values):
        return sorted(values, key=lambda x: x.lane)

    class Config:
        orm_mode = True
