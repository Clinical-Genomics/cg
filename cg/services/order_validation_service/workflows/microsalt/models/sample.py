from pydantic import Field

from cg.constants.constants import GenomeVersion
from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.constants import TissueBlockEnum
from cg.services.order_validation_service.models.sample import Sample


class MicroSaltSample(Sample):
    control: ControlEnum | None = None
    elution_buffer: str | None = None
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    concentration_ng_ul: float | None = None
