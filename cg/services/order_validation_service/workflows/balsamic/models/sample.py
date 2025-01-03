from pydantic import BeforeValidator, Field, PrivateAttr
from typing_extensions import Annotated

from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.constants import ElutionBuffer, TissueBlockEnum
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import parse_buffer, parse_control


class BalsamicSample(Sample):
    age_at_sampling: float | None = None
    capture_kit: str | None = None
    _case_name: str = PrivateAttr(default="")
    comment: str | None = None
    concentration_ng_ul: float | None = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer | None, BeforeValidator(parse_buffer)] = None
    formalin_fixation_time: int | None = None
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    post_formalin_fixation_time: int | None = None
    require_qc_ok: bool
    sex: SexEnum
    source: str
    status: StatusEnum | None = None
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
    tissue_block_size: TissueBlockEnum | None = None
    tumour: bool
    tumour_purity: int | None = None
