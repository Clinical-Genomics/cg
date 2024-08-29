from pydantic import Field
from cg.constants.constants import GenomeVersion
from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.constants import ElutionBuffer, TissueBlockEnum
from cg.services.order_validation_service.models.sample import Sample


class BalsamicSample(Sample):
    age_at_sampling: float | None = None
    capture_kit: str | None = None
    comment: str | None = None
    concentration_ng_ul: float | None = None
    control: ControlEnum | None = None
    elution_buffer: ElutionBuffer
    formalin_fixation_time: int | None = None
    is_tumour: bool
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    post_formalin_fixation_time: int | None = None
    reference_genome: GenomeVersion
    sex: SexEnum
    source: str
    status: StatusEnum | None = None
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tissue_block_size: TissueBlockEnum | None = None
    tumour_purity: int | None = None
