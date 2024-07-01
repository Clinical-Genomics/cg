from pydantic import BaseModel, Field

from cg.constants import DataDelivery
from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.validation_service.models.order_sample import OrderSample


class OrderCase(BaseModel):
    data_delivery: DataDelivery
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: list[OrderSample]
