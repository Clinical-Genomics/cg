from pydantic import Field

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import ExtractionMethod
from cg.services.order_validation_service.models.sample import Sample


class MicrosaltSample(Sample):
    control: ControlEnum | None = None
    elution_buffer: str
    extraction_method: ExtractionMethod
    organism: str
    priority: PriorityEnum
    quantity: int | None = None
    reference_genome: str = Field(max_length=255)
    sample_concentration: float | None = None
