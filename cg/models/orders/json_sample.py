from cg.models.orders.sample_base import OrderSample
from pydantic import Field


class JsonSample(OrderSample):
    case_id: str = Field(None, alias="family_name")
