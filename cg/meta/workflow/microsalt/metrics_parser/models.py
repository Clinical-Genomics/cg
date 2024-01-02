from typing import Annotated
from pydantic import BaseModel, BeforeValidator


def empty_str_to_none(v: str) -> str | None:
    return v or None


class PicardMarkduplicate(BaseModel):
    insert_size: Annotated[int | None, BeforeValidator(empty_str_to_none)]
    duplication_rate: Annotated[float | None, BeforeValidator(empty_str_to_none)]


class MicrosaltSamtoolsStats(BaseModel):
    total_reads: Annotated[int | None, BeforeValidator(empty_str_to_none)]
    mapped_rate: Annotated[float | None, BeforeValidator(empty_str_to_none)]
    average_coverage: Annotated[float | None, BeforeValidator(empty_str_to_none)]
    coverage_10x: Annotated[float | None, BeforeValidator(empty_str_to_none)]


class SampleMetrics(BaseModel):
    picard_markduplicate: PicardMarkduplicate
    microsalt_samtools_stats: MicrosaltSamtoolsStats


class QualityMetrics(BaseModel):
    samples: dict[str, SampleMetrics]
