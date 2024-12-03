from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import IndexEnum
from cg.services.order_validation_service.models.sample import Sample


class FluffySample(Sample):
    control: ControlEnum | None = None
    priority: PriorityEnum
    index: IndexEnum
    index_number: str | None
    pool: str
    pool_concentration: float
    concentration_sample: float | None = None
