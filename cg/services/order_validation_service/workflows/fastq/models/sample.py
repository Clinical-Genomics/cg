from cg.models.orders.sample_base import PriorityEnum, SexEnum
from cg.services.order_validation_service.models.sample import Sample


class FastqSample(Sample):
    concentration_ng_ul: float | None = None
    elution_buffer: ElutionBufferEnum
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool
    sex: SexEnum
    source: str  # Required if no internal id
    tumour: bool = False
