from typing import Optional, Any, List

from cg.constants import DataDelivery, Pipeline
from cg.models.orders.sample_base import OrderSample
from pydantic import field_validator, constr


class JsonSample(OrderSample):
    cohorts: Optional[List[str]] = None
    concentration: Optional[str] = None
    concentration_sample: Optional[str] = None
    control: Optional[str] = None
    data_analysis: Pipeline = Pipeline.MIP_DNA
    data_delivery: DataDelivery = DataDelivery.SCOUT
    index: Optional[str] = None
    panels: Optional[List[str]] = None
    quantity: Optional[str] = None
    synopsis: Optional[str] = None
    well_position: Optional[constr(pattern=r"[A-H]:[0-9]+")] = None

    @field_validator("synopsis", mode="before")
    @classmethod
    def join_list(cls, value: Any):
        if isinstance(value, list):
            return "".join(value)
        return value

    @field_validator("well_position", mode="before")
    @classmethod
    def convert_well(cls, value: str):
        if not value:
            return None
        if ":" in value:
            return value
        return ":".join([value[0], value[1:]])
