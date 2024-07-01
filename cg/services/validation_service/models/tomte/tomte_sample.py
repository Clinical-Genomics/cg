from pydantic import Field

from cg.constants.constants import GenomeVersion
from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum, StatusEnum
from cg.services.validation_service.constants import TissueBlockEnum
from cg.services.validation_service.models.order_sample import OrderSample


class TomteSample(OrderSample):
    age_at_sampling: float | None = None
    control: ControlEnum | None = None
    elution_buffer: str | None = None
    father: str | None = Field(None, pattern=NAME_PATTERN)
    formalin_fixation_time: int | None = None
    mother: str = Field(None, pattern=NAME_PATTERN)
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    post_formalin_fixation_time: int | None = None
    reference_genome: GenomeVersion
    sex: SexEnum = SexEnum.unknown
    source: str | None
    status: StatusEnum
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tissue_block_size: TissueBlockEnum | None = None
    concentration_ng_ul: float | None = None
