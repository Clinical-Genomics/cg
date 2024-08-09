from pydantic import BaseModel, ConfigDict, Field

from cg.constants.constants import DataDelivery
from cg.constants.priority import PriorityTerms
from cg.models.orders.sample_base import NAME_PATTERN


class Case(BaseModel):
    data_delivery: DataDelivery
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    priority: PriorityTerms = PriorityTerms.STANDARD

    model_config = ConfigDict(str_min_length=1)
