from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ValidationError


def empty_str_to_none(value: str) -> str | None:
    if not isinstance(value, str):
        raise TypeError(f"Expected a string, but got {type(value).__name__}")
    return value or None


def str_to_bool(v: str) -> bool:
    if v == "TRUE":
        return True
    elif v == "FALSE":
        return False
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


class SamplesResultsMetrics(BaseModel):
    samples: dict[str, SampleResults]
