from pydantic import Field

from cg.models.orders.sample_base import (
    NAME_PATTERN,
    ControlEnum,
    PriorityEnum,
)
from cg.services.order_validation_service.models.sample import Sample


class MicroSaltSample(Sample):
    control: ControlEnum | None = None
    elution_buffer: str | None = None
    extraction_method: str | None = None
    organism: str | None = Field(default=None, max_length=32)
    priority: PriorityEnum | None = None
    quantity: int | None = None
    reference_genome: str | None = Field(default=None, max_length=255)
    sample_concentration: float | None = None
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
