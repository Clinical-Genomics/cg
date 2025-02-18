from pydantic import BeforeValidator, constr
from typing_extensions import Annotated

from cg.constants import DataDelivery, Workflow
from cg.models.orders.sample_base import OrderSample
from cg.models.orders.validators.json_sample_validators import convert_well, join_list


class JsonSample(OrderSample):
    cohorts: list[str] | None = None
    concentration: str | None = None
    concentration_ng_ul: str | None = None
    concentration_sample: str | None = None
    control: str | None = None
    data_analysis: Workflow = Workflow.MIP_DNA
    data_delivery: DataDelivery = DataDelivery.SCOUT
    index: str | None = None
    panels: list[str] | None = None
    quantity: str | None = None
    synopsis: Annotated[str | None, BeforeValidator(join_list)] = None
    well_position: Annotated[
        constr(pattern=r"^[A-H]:(1[0-2]|[1-9])$") | None, BeforeValidator(convert_well)
    ] = None
