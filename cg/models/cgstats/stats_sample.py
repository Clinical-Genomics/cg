from typing import List, Set

from pydantic import field_validator, ConfigDict, BaseModel, Field, validator


class Unaligned(BaseModel):
    lane: int
    read_count: int = Field(..., alias="readcounts")
    yield_mb: int
    passed_filter_pct: float

    q30_bases_pct: float
    mean_quality_score: float
    model_config = ConfigDict(from_attributes=True)


class StatsSample(BaseModel):
    sample_name: str = Field(..., alias="samplename")
    unaligned: List[Unaligned]
    lanes: List[int] = []
    read_count_sum: int = 0
    sum_yield: int = 0

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("lanes", always=True)
    def set_lanes(cls, _, values: dict) -> List[int]:
        """Set the number of pass filter clusters"""
        unaligned_reads: List[Unaligned] = values["unaligned"]
        lanes_found: Set[int] = set()
        for read in unaligned_reads:
            lanes_found.add(read.lane)
        return list(lanes_found)

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("read_count_sum", always=True)
    def set_read_count(cls, _, values: dict):
        unaligned_reads: List[Unaligned] = values["unaligned"]
        count: int = 0
        for read in unaligned_reads:
            count += read.read_count
        return count

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("sum_yield", always=True)
    def set_sum_yield(cls, _, values: dict):
        unaligned_reads: List[Unaligned] = values["unaligned"]
        count: int = 0
        for read in unaligned_reads:
            count += read.yield_mb
        return count

    @field_validator("unaligned")
    @classmethod
    def sort_unaligned(cls, values):
        return sorted(values, key=lambda x: x.lane)

    model_config = ConfigDict(from_attributes=True)
