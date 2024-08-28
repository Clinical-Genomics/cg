from datetime import datetime

from pydantic import BaseModel

from cg.constants.subject import Sex


class ApplicationVersionDTO(BaseModel):
    id: int
    version: int | None = None
    valid_from: datetime | None = None
    price_standard: int | None = None
    price_priority: int | None = None
    price_express: int | None = None
    price_research: int | None = None
    price_clinical_trials: int | None = None
    comment: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    application_id: int | None = None


class ApplicationDTO(BaseModel):
    id: int
    tag: str | None = None
    prep_category: str | None = None
    is_external: bool | None = None
    description: str | None = None
    is_accredited: bool | None = None
    turnaround_time: int | None = None
    minimum_order: int | None = None
    sequencing_depth: int | None
    min_sequencing_depth: int | None = None
    target_reads: int | None = None
    percent_reads_guaranteed: int | None = None
    sample_amount: int | None = None
    sample_volume: str | None = None
    sample_concentration: str | None = None
    sample_concentration_minimum: float | None = None
    sample_concentration_maximum: float | None = None
    sample_concentration_minimum_cfdna: float | None = None
    sample_concentration_maximum_cfdna: float | None = None
    priority_processing: bool | None = None
    details: str | None = None
    limitations: str | None = None
    percent_kth: int | None = None
    comment: str | None = None
    is_archived: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomerDto(BaseModel):
    internal_id: str
    name: str


class SampleDTO(BaseModel):
    application: ApplicationDTO | None = None
    application_version: ApplicationVersionDTO | None = None
    name: str | None = None
    internal_id: str | None = None
    data_analysis: str | None = None
    data_delivery: str | None = None
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
    is_tumour: bool | None = None
    reference_genome: str | None = None
    customer: CustomerDto | None = None


class SamplesResponse(BaseModel):
    samples: list[SampleDTO]
    total: int
