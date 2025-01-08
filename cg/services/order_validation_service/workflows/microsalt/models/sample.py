from pydantic import BeforeValidator, Field, PrivateAttr
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import ElutionBuffer, ExtractionMethod
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import (
    parse_buffer,
    parse_control,
    parse_extraction_method,
)


class MicrosaltSample(Sample):
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    extraction_method: Annotated[ExtractionMethod, BeforeValidator(parse_extraction_method)]
    organism: str
    priority: PriorityEnum
    reference_genome: str = Field(max_length=255)
    _verified_organism: str | None = PrivateAttr(default=None)
