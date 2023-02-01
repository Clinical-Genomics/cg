from typing import Optional, Any, List

from cg.constants import DataDelivery, Pipeline
from cg.models.orders.sample_base import OrderSample
from pydantic import constr, validator


class JsonSample(OrderSample):
    cohorts: Optional[List[str]]
    concentration: Optional[str]
    concentration_sample: Optional[str]
    control: Optional[str]
    data_analysis: Pipeline = Pipeline.MIP_DNA
    data_delivery: DataDelivery = DataDelivery.SCOUT
    index: Optional[str]
    panels: Optional[List[str]]
    quantity: Optional[str]
    synopsis: Optional[str]
    well_position: Optional[constr(regex=r"[A-H]:[0-9]+")]

    @validator("synopsis", pre=True)
    def join_list(cls, value: Any):
        if isinstance(value, list):
            return "".join(value)
        return value

    @validator("well_position", pre=True)
    def convert_well(cls, value: str):
        if not value:
            return None
        if ":" in value:
            return value
        return ":".join([value[0], value[1:]])
