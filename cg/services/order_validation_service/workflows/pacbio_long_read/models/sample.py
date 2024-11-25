from pydantic import Field

from cg.models.orders.sample_base import NAME_PATTERN, PriorityEnum, SexEnum
from cg.services.order_validation_service.models.sample import Sample


class PacbioSample(Sample):
    concentration_ng_ul: float | None = None
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool
    sex: SexEnum
    source: str
    subject_id: str | None = Field(pattern=NAME_PATTERN, max_length=128)
    tumour: bool = False
