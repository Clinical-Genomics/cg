from pydantic import Field

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.models.sample import Sample


class fluffySample(Sample):
    control: ControlEnum | None = None
    priority: PriorityEnum
    index: str
    index_number: str | None
    pool: str | None
    pool_concentration: float | None
    sample_concentration: float | None = None
