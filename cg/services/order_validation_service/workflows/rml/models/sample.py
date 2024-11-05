from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.models.sample import Sample


class RmlSample(Sample):
    control: ControlEnum | None = None
    index: str
    index_number: int
    pool: str | None = None
    pool_concentration: float | None = None
    priority: PriorityEnum
    sample_concentration: float | None = None
