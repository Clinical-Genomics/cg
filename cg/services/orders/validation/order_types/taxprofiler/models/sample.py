from typing import Any

from pydantic import BeforeValidator, model_validator
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_buffer, parse_control


class TaxprofilerSample(Sample):
    concentration_ng_ul: float | None = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool = False
    source: str

    @model_validator(mode="before")
    def set_other_source(cls, data: Any) -> Any:
        """When source is sent as 'other', we should instead set the value sent as 'source_comment'."""
        if isinstance(data, dict) and data.get("source") == "other":
            data["source"] = data.get("source_comment")
        return data
