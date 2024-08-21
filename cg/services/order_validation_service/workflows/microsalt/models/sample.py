from pydantic import Field

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import ExtractionMethod
from cg.services.order_validation_service.models.sample import Sample


class MicrosaltSample(Sample):
    control: ControlEnum | None = None
    elution_buffer: str | None = None
    extraction_method: ExtractionMethod | None = None
    organism: str | None = None
    priority: PriorityEnum | None = None
    quantity: int | None = None
    reference_genome: str | None = Field(default=None, max_length=255)
    sample_concentration: float | None = None
