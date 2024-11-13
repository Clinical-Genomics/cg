from pydantic import Field

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.workflows.fluffy.constants import (
    fluffyIndexEnum,
)


class fluffySample(Sample):
    control: ControlEnum | None = None
    priority: PriorityEnum
    index: fluffyIndexEnum
    index_number: str | None
    pool: str | None
    pool_concentration: float | None
    concentration_sample: float | None = None
