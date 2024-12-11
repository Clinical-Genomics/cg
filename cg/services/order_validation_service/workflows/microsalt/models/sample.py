from pydantic import BeforeValidator, Field
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import ElutionBuffer, ExtractionMethod
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import parse_buffer


class MicrosaltSample(Sample):
    control: ControlEnum | None = None
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    extraction_method: ExtractionMethod
    organism: str
    priority: PriorityEnum
    reference_genome: str = Field(max_length=255)
