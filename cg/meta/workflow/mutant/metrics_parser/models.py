from typing import Annotated
from pydantic import BaseModel, BeforeValidator, Field, ValidationError


def empty_str_to_none(value: str) -> str | None:
    if not isinstance(value, str):
        raise TypeError(f"Expected a string, but got {type(value).__name__}")
    return value or None


def str_to_bool(value: str) -> bool:
    if value == "TRUE":
        return True
    elif value == "FALSE":
        return False
    raise ValidationError(f"String {value} cannot be turned to bool.")


class SampleResults(BaseModel):
    sample_name: str = Field(alias="Sample")
    selection: str = Field(alias="Selection")
    region_code: str = Field(alias="Region Code")
    ticket: Annotated[int | None, BeforeValidator(empty_str_to_none)] = Field(alias="Ticket")
    pct_n_bases: Annotated[float | None, BeforeValidator(empty_str_to_none)] = Field(
        alias="%N_bases"
    )
    pct_10x_coverage: Annotated[float | None, BeforeValidator(empty_str_to_none)] = Field(
        alias="%10X_coverage"
    )
    qc_pass: Annotated[bool, BeforeValidator(str_to_bool)] = Field(alias="QC_pass")
    lineage: str = Field(alias="Lineage")
    pangolin_data_version: str = Field(alias="Pangolin_data_version")
    voc: str = Field(alias="VOC")
    mutations: Annotated[str | None, BeforeValidator(empty_str_to_none)] = Field(alias="Mutations")


class SamplesResultsMetrics(BaseModel):
    samples: dict[str, SampleResults]
