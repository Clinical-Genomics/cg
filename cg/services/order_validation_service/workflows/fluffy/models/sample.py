from pydantic import BeforeValidator
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import IndexEnum
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import parse_control


class FluffySample(Sample):
    concentration_sample: float | None = None
    container: None = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    priority: PriorityEnum
    index: IndexEnum
    index_number: str | None
    pool: str
    pool_concentration: float
    rml_plate_name: str | None = None
    well_position_rml: str | None = None
