from typing import Optional

from pydantic import BeforeValidator, constr
from typing_extensions import Annotated

from cg.constants import DataDelivery, Pipeline
from cg.models.orders.sample_base import OrderSample
from cg.models.orders.validators.json_sample_validators import convert_well, join_list


class JsonSample(OrderSample):
    cohorts: Optional[list[str]] = None
    concentration: Optional[str] = None
    concentration_sample: Optional[str] = None
    control: Optional[str] = None
    data_analysis: Pipeline = Pipeline.MIP_DNA
    data_delivery: DataDelivery = DataDelivery.SCOUT
    index: Optional[str] = None
    panels: Optional[list[str]] = None
    quantity: Optional[str] = None
    synopsis: Annotated[Optional[str], BeforeValidator(join_list)] = None
    well_position: Annotated[
        Optional[constr(pattern=r"^[A-H]:(1[0-2]|[1-9])$")], BeforeValidator(convert_well)
    ] = None
