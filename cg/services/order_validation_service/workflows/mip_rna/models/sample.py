from pydantic import Field

from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum
from cg.services.order_validation_service.constants import TissueBlockEnum
from cg.services.order_validation_service.models.sample import Sample


class MipRnaSample(Sample):
    age_at_sampling: float | None = None
    concentration_ng_ul: float | None = None
    control: ControlEnum
    elution_buffer: str | None = None
    formalin_fixation_time: int | None = None
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    post_formalin_fixation_time: int | None = None
    sex: SexEnum
    source: str
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tissue_block_size: TissueBlockEnum | None = None
