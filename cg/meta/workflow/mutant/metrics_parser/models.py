from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ValidationError

def empty_str_to_none(v: str) -> str | None:
    return v or None


def str_to_bool(v: str) -> bool:
    if v == "TRUE":
        return True
    elif v == "FALSE":
        return False
    else:
        raise ValidationError

class SampleResults(BaseModel):
    sample_name: str
    selection: str
    region_code: str
    ticket: Annotated[int | None, BeforeValidator(empty_str_to_none)]
    pct_n_bases: Annotated[float | None, BeforeValidator(empty_str_to_none)]
    pct_10x_coverage: Annotated[float | None, BeforeValidator(empty_str_to_none)]
    qc_pass: Annotated[bool | None, BeforeValidator(str_to_bool)]
    lineage: str
    pangolin_data_version: str
    voc: str
    mutations: Annotated[str | None, BeforeValidator(empty_str_to_none)]


class SampleMetadata(BaseModel):
    sample_internal_id: str
    sample_name: str
    is_control: bool
    reads: int


class SampleMetrics(BaseModel):
    sample_results: SampleResults
    sample_metadata: SampleMetadata


class QualityMetrics(BaseModel):
    samples: dict[str, SampleMetrics]
