from enum import StrEnum

from pydantic import BaseModel, BeforeValidator, ConfigDict, constr
from typing_extensions import Annotated

from cg.constants import DataDelivery, Workflow
from cg.models.orders.validators.sample_base_validators import snake_case
from cg.store.models import Application, Case, Customer, Pool, Sample


class ControlEnum(StrEnum):
    not_control = ""
    positive = "positive"
    negative = "negative"


class SexEnum(StrEnum):
    male = "male"
    female = "female"
    unknown = "unknown"


class PriorityEnum(StrEnum):
    research = "research"
    standard = "standard"
    priority = "priority"
    express = "express"
    clinical_trials = "clinical_trials"


class ContainerEnum(StrEnum):
    no_container = "No container"
    plate = "96 well plate"
    tube = "Tube"


class StatusEnum(StrEnum):
    affected = "affected"
    unaffected = "unaffected"
    unknown = "unknown"


NAME_PATTERN = r"^[A-Za-z0-9-]*$"


class OrderSample(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, populate_by_name=True, coerce_numbers_to_str=True
    )
    age_at_sampling: str | None = None
    application: constr(max_length=Application.tag.property.columns[0].type.length)
    capture_kit: str | None = None
    collection_date: str | None = None
    comment: constr(max_length=Sample.comment.property.columns[0].type.length) | None = None
    concentration: float | None = None
    concentration_ng_ul: float | None = None
    concentration_sample: float | None = None
    container: ContainerEnum | None = None
    container_name: str | None = None
    control: str | None = None
    customer: constr(max_length=Customer.internal_id.property.columns[0].type.length) | None = None
    custom_index: str | None = None
    data_analysis: Workflow
    data_delivery: DataDelivery
    elution_buffer: str | None = None
    extraction_method: str | None = None
    family_name: (
        constr(
            pattern=NAME_PATTERN,
            min_length=2,
            max_length=Case.name.property.columns[0].type.length,
        )
        | None
    ) = None
    father: (
        constr(pattern=NAME_PATTERN, max_length=Sample.name.property.columns[0].type.length) | None
    ) = None
    formalin_fixation_time: int | None = None
    index: str | None = None
    index_number: str | None = None
    index_sequence: str | None = None
    internal_id: constr(max_length=Sample.internal_id.property.columns[0].type.length) | None = None
    lab_code: str | None = None
    mother: (
        constr(pattern=NAME_PATTERN, max_length=Sample.name.property.columns[0].type.length) | None
    ) = None
    name: constr(
        pattern=NAME_PATTERN,
        min_length=2,
        max_length=Sample.name.property.columns[0].type.length,
    )
    organism: str | None = None
    organism_other: str | None = None
    original_lab: str | None = None
    original_lab_address: str | None = None
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    pool: constr(max_length=Pool.name.property.columns[0].type.length) | None = None
    post_formalin_fixation_time: int | None = None
    pre_processing_method: str | None = None
    priority: Annotated[PriorityEnum, BeforeValidator(snake_case)] = PriorityEnum.standard
    primer: str | None = None
    quantity: int | None = None
    reagent_label: str | None = None
    reference_genome: (
        constr(max_length=Sample.reference_genome.property.columns[0].type.length) | None
    ) = None
    region: str | None = None
    region_code: str | None = None
    require_qc_ok: bool = False
    rml_plate_name: str | None = None
    selection_criteria: str | None = None
    sex: SexEnum = SexEnum.unknown
    source: str | None = None
    status: StatusEnum = StatusEnum.unknown
    subject_id: (
        constr(pattern=NAME_PATTERN, max_length=Sample.subject_id.property.columns[0].type.length)
        | None
    ) = None
    tissue_block_size: str | None = None
    tumour: bool = False
    tumour_purity: int | None = None
    verified_organism: bool | None = None
    volume: str | None = None
    well_position: str | None = None
    well_position_rml: str | None = None
