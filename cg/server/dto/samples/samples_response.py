from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from cg.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.constants.subject import Sex
from cg.store.models import Sample


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


class UnhandledSample(BaseModel):
    internal_id: str
    last_sequenced_at: datetime
    lims_status: LimsStatus
    ticket: int | Literal["unknown"]
    workflow: Workflow | Literal["unknown"]


class UnhandledSamplesResponse(BaseModel):
    samples: list[UnhandledSample]
    total: int

    @classmethod
    def from_samples(cls, samples: list[Sample], total: int) -> "UnhandledSamplesResponse":
        """
        Creates an UnhandledSamplesResponse object from a list of database samples.
        Raises:
            ValidationError if any sample is not linked to a case or if it has not been sequenced.
        """
        unhandled_samples = []
        for sample in samples:
            unhandled_samples.append(
                UnhandledSample(
                    internal_id=sample.internal_id,
                    last_sequenced_at=sample.last_sequenced_at,  # type: ignore
                    lims_status=sample.lims_status,
                    ticket=sample.ticket_id_from_original_order or "unknown",
                    workflow=sample.original_workflow or "unknown",
                )
            )
        return cls(samples=unhandled_samples, total=total)
