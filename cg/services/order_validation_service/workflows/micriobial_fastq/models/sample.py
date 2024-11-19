from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import ElutionBuffer
from cg.services.order_validation_service.models.sample import Sample


class MicrobialFastqSample(Sample):
    control: ControlEnum | None = None
    elution_buffer: ElutionBuffer
    priority: PriorityEnum
    quantity: int | None = None
    require_qc_ok: bool
