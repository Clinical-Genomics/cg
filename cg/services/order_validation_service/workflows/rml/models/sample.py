from pydantic import BeforeValidator
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import IndexEnum
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import parse_control, set_to_none


class RmlSample(Sample):
    concentration: float
    container: Annotated[None, BeforeValidator(set_to_none)] = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    index: IndexEnum
    index_number: int | None = None
    index_sequence: str | None = None
    pool: str
    priority: PriorityEnum
    rml_plate_name: str | None = None
    sample_concentration: float | None = None
    volume: int
    well_position_rml: str | None = None
