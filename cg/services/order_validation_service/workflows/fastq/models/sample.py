from pydantic import Field

from cg.models.orders.sample_base import NAME_PATTERN, PriorityEnum, SexEnum
from cg.services.order_validation_service.constants import ElutionBuffer
from cg.services.order_validation_service.models.sample import Sample


class FastqSample(Sample):
    capture_kit: str | None = None
    concentration_ng_ul: float | None = None
    elution_buffer: ElutionBuffer
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool
    sex: SexEnum
    source: str
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tumour: bool = False
