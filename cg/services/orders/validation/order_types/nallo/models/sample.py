from typing import Annotated, Any

from pydantic import BeforeValidator, Field, model_validator

from cg.models.orders.sample_base import NAME_PATTERN, SexEnum, StatusEnum
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_buffer


class NalloSample(Sample):
    elution_buffer: Annotated[ElutionBuffer | None, BeforeValidator(parse_buffer)] = None
    father: str | None = Field(None, pattern=NAME_PATTERN)
    mother: str | None = Field(None, pattern=NAME_PATTERN)
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    require_qc_ok: bool = False
    sex: SexEnum
    source: str
    status: StatusEnum
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)

    @model_validator(mode="before")
    def set_other_source(cls, data: Any) -> Any:
        """When source is sent as 'other', we should instead set the value sent as 'source_comment'."""
        if isinstance(data, dict):
            if data.get("source") == "other":
                data["source"] = data.get("source_comment")
        return data
