from typing import Any

from pydantic import model_validator

from cg.models.orders.sample_base import PriorityEnum, SexEnum
from cg.services.orders.validation.models.sample import Sample


class PacbioSample(Sample):
    concentration_ng_ul: float | None = None
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool = False
    sex: SexEnum
    source: str
    tumour: bool = False

    @model_validator(mode="before")
    def set_other_source(cls, data: Any) -> Any:
        """When source is sent as 'other', we should instead set the value sent as 'source_comment'."""
        if isinstance(data, dict) and data.get("source") == "other":
            data["source"] = data.get("source_comment")
        return data
