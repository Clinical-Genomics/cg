from typing import Any

from pydantic import BeforeValidator, Field, model_validator
from typing_extensions import Annotated

from cg.models.orders.sample_base import NAME_PATTERN, PriorityEnum, SexEnum
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_buffer


class FastqSample(Sample):
    capture_kit: str | None = None
    concentration_ng_ul: float | None = None
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool = False
    sex: SexEnum
    source: str
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tumour: bool = False

    @model_validator(mode="before")
    def set_other_source(cls, data: Any) -> Any:
        """When source is sent as 'other', we should instead set the value sent as 'source_comment'."""
        if isinstance(data, dict):
            if data.get("source") == "other":
                data["source"] = data.get("source_comment")
        return data
