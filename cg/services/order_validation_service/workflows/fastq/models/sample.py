from pydantic import BeforeValidator, Field
from typing_extensions import Annotated

from cg.models.orders.sample_base import NAME_PATTERN, PriorityEnum, SexEnum
from cg.services.order_validation_service.constants import ElutionBuffer
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import parse_buffer


class FastqSample(Sample):
    capture_kit: str | None = None
    concentration_ng_ul: float | None = None
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool
    sex: SexEnum
    source: str
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tumour: bool = False
