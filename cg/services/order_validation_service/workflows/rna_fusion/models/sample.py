from pydantic import Field

from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.constants import TissueBlockEnum
from cg.services.order_validation_service.models.sample import Sample


class RnaFusionSample(Sample):
    age_at_sampling: float | None = None
    concentration_ng_ul: float | None = None
    control: ControlEnum | None
    elution_buffer: ElutionBuffer | None = None
    formalin_fixation_time: int | None = None
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    post_formalin_fixation_time: int | None = None
    require_qc_ok: bool
    sex: SexEnum
    source: str
    status: StatusEnum
    subject_id: str = Field(pattern=NAME_PATTERN, min_length=1, max_length=128)
    tissue_block_size: TissueBlockEnum | None = None
