from pydantic import BaseModel

from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import OrderSample


class OrderCase(BaseModel):
    name: str
    priority: PriorityTerms = PriorityTerms.STANDARD
    samples: list[OrderSample]
