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
