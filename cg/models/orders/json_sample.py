from typing import List, Optional

from cg.constants import DataDelivery, Pipeline
from cg.models.orders.sample_base import OrderSample
from pydantic import Field, constr, validator


class JsonSample(OrderSample):
    case_id: str = Field(None, alias="family_name")
    concentration: Optional[str]
    concentration_sample: Optional[str]
    data_analysis: Pipeline = Pipeline.MIP_DNA
    data_delivery: DataDelivery = DataDelivery.SCOUT
    index: Optional[str]
    quantity: Optional[str]
    synopsis: Optional[List[str]]
    well_position: Optional[constr(regex=r"[A-H]:[0-9]+")]

    @validator("priority", pre=True)
    def make_lower(cls, value: str):
        return value.lower()

    @validator("well_position", pre=True)
    def convert_well(cls, value: str):
        if not value:
            return None
        if ":" in value:
            return value
        return ":".join([value[0], value[1:]])
