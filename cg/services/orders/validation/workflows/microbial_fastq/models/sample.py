from pydantic import BeforeValidator
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.orders.validation.constants import ElutionBuffer
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_buffer, parse_control


class MicrobialFastqSample(Sample):
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    priority: PriorityEnum
    quantity: int | None = None
    volume: int
