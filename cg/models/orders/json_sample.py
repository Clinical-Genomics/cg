from typing import Any, List, Optional

from cg.constants import DataDelivery, Pipeline
from cg.models.orders.sample_base import OrderSample
from pydantic import BeforeValidator, constr
from typing_extensions import Annotated


def join_list(potential_list: Any):
    """If given a list, it is converted to a string by joining its entries.
    Else the argument is returned as is."""
    return "".join(potential_list) if isinstance(potential_list, list) else potential_list


def convert_well(value: str):
    if not value:
        return None
    return value if ":" in value else ":".join([value[0], value[1:]])


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
    synopsis: Annotated[Optional[str], BeforeValidator(join_list)] = None
    well_position: Annotated[
        Optional[constr(pattern=r"[A-H]:[0-9]+")], BeforeValidator(convert_well)
    ] = None
