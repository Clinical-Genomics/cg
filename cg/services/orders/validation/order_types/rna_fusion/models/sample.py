from pydantic import BeforeValidator, Field, field_validator
from typing_extensions import Annotated

from cg.models.orders.sample_base import NAME_PATTERN, ControlEnum, SexEnum
from cg.services.orders.validation.constants import ElutionBuffer, TissueBlockEnum
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_buffer, parse_control

TUMOUR_ERROR_MESSAGE: str = "RNAFUSION samples must always be tumour samples"


class RNAFusionSample(Sample):
    age_at_sampling: float | None = None
    concentration_ng_ul: float | None = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer | None, BeforeValidator(parse_buffer)] = None
    formalin_fixation_time: int | None = None
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    post_formalin_fixation_time: int | None = None
    require_qc_ok: bool = False
    sex: SexEnum
    source: str
    subject_id: str = Field(pattern=NAME_PATTERN, min_length=1, max_length=128)
    tissue_block_size: TissueBlockEnum | None = None
    tumour: bool = True

    @field_validator("tumour")
    @classmethod
    def validate_tumour_is_true(cls, v):
        if v is not True:
            raise ValueError(TUMOUR_ERROR_MESSAGE)
        return v

    def __setattr__(self, name, value):
        if name == "tumour" and hasattr(self, name):
            raise ValueError(TUMOUR_ERROR_MESSAGE)
        super().__setattr__(name, value)

    def model_copy(self, *args, update=None, **kwargs):
        if update and "tumour" in update and update["tumour"] is not True:
            raise ValueError(TUMOUR_ERROR_MESSAGE)
        return super().model_copy(*args, update=update, **kwargs)
