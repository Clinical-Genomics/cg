from pydantic import BaseModel

from cg.constants.subject import Sex


class CustomerDto(BaseModel):
    internal_id: str
    name: str


class SampleDTO(BaseModel):
    name: str | None = None
    internal_id: str | None = None
    data_analysis: str | None = None
    data_delivery: str | None = None
    application: str | None = None
    mother: str | None = None
    father: str | None = None
    family_name: str | None = None
    case_internal_id: str | None = None
    require_qc_ok: bool | None = None
    sex: Sex | None = None
    source: str | None = None
    priority: str | None = None
    formalin_fixation_time: int | None = None
    post_formalin_fixation_time: int | None = None
    tissue_block_size: str | None = None
    cohorts: list[str] | None = None
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    subject_id: str | None = None
    synopsis: str | None = None
    age_at_sampling: int | None = None
    comment: str | None = None
    control: str | None = None
    elution_buffer: str | None = None
    container: str | None = None
    container_name: str | None = None
    well_position: str | None = None
    volume: int | None = None
    concentration_ng_ul: int | None = None
    panels: list[str] | None = None
    status: str | None = None
    tumour: bool | None = None
    reference_genome: str | None = None
    customer: CustomerDto | None = None


class SamplesResponse(BaseModel):
    samples: list[SampleDTO]
    total: int
