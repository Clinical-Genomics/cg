from pydantic import BeforeValidator, Field
from typing_extensions import Annotated

from cg.models.orders.sample_base import ContainerEnum, ControlEnum, PriorityEnum
from cg.services.orders.validation.constants import IndexEnum
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_control


class FluffySample(Sample):
    concentration: float
    concentration_sample: float | None = None
    container: ContainerEnum | None = Field(default=None, exclude=True)
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    priority: PriorityEnum
    index: IndexEnum
    index_number: int | None = None
    index_sequence: str | None = None
    pool: str
    rml_plate_name: str | None = None
    volume: int
    well_position_rml: str | None = None
