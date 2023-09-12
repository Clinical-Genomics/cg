from enum import Enum
from typing import List, Optional

from cg.constants import DataDelivery, Pipeline
from cg.models.orders.validators.sample_base_validators import snake_case
from cg.store.models import Application, Customer, Family, Pool, Sample
from pydantic import BaseModel, BeforeValidator, ConfigDict, constr
from typing_extensions import Annotated


class ControlEnum(str, Enum):
    not_control = ""
    positive = "positive"
    negative = "negative"


class SexEnum(str, Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


class PriorityEnum(str, Enum):
    research = "research"
    standard = "standard"
    priority = "priority"
    express = "express"
    clinical_trials = "clinical_trials"


class ContainerEnum(str, Enum):
    no_container = "No container"
    plate = "96 well plate"
    tube = "Tube"


class StatusEnum(str, Enum):
    affected = "affected"
    unaffected = "unaffected"
    unknown = "unknown"


NAME_PATTERN = r"^[A-Za-z0-9-]*$"


class OrderSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    age_at_sampling: Annotated[
        Optional[str], BeforeValidator(lambda x: str(x) if x else None)
    ] = None
    application: constr(max_length=Application.tag.property.columns[0].type.length)
    capture_kit: Optional[str] = None
    collection_date: Optional[str] = None
    comment: Optional[constr(max_length=Sample.comment.property.columns[0].type.length)] = None
    concentration: Optional[float] = None
    concentration_sample: Optional[float] = None
    container: Optional[ContainerEnum] = None
    container_name: Optional[str] = None
    control: Optional[str] = None
    customer: Optional[
        constr(max_length=Customer.internal_id.property.columns[0].type.length)
    ] = None
    custom_index: Optional[str] = None
    data_analysis: Pipeline
    data_delivery: DataDelivery
    elution_buffer: Optional[str] = None
    extraction_method: Optional[str] = None
    family_name: Optional[
        constr(
            pattern=NAME_PATTERN,
            min_length=2,
            max_length=Family.name.property.columns[0].type.length,
        )
    ] = None
    father: Optional[
        constr(pattern=NAME_PATTERN, max_length=Sample.name.property.columns[0].type.length)
    ] = None
    formalin_fixation_time: Optional[int] = None
    index: Optional[str] = None
    index_number: Optional[str] = None
    index_sequence: Optional[str] = None
    internal_id: Optional[
        constr(max_length=Sample.internal_id.property.columns[0].type.length)
    ] = None
    lab_code: Optional[str] = None
    mother: Optional[
        constr(pattern=NAME_PATTERN, max_length=Sample.name.property.columns[0].type.length)
    ] = None
    name: constr(
        pattern=NAME_PATTERN,
        min_length=2,
        max_length=Sample.name.property.columns[0].type.length,
    )
    organism: Optional[str] = None
    organism_other: Optional[str] = None
    original_lab: Optional[str] = None
    original_lab_address: Optional[str] = None
    phenotype_groups: Optional[List[str]] = None
    phenotype_terms: Optional[List[str]] = None
    pool: Optional[constr(max_length=Pool.name.property.columns[0].type.length)] = None
    post_formalin_fixation_time: Optional[int] = None
    pre_processing_method: Optional[str] = None
    priority: Annotated[PriorityEnum, BeforeValidator(snake_case)] = PriorityEnum.standard
    quantity: Optional[int] = None
    reagent_label: Optional[str] = None
    reference_genome: Optional[
        constr(max_length=Sample.reference_genome.property.columns[0].type.length)
    ] = None
    region: Optional[str] = None
    region_code: Optional[str] = None
    require_qc_ok: bool = False
    rml_plate_name: Optional[str] = None
    selection_criteria: Optional[str] = None
    sex: SexEnum = SexEnum.unknown
    source: Optional[str] = None
    status: StatusEnum = StatusEnum.unknown
    subject_id: Optional[
        constr(pattern=NAME_PATTERN, max_length=Sample.subject_id.property.columns[0].type.length)
    ] = None
    tissue_block_size: Optional[str] = None
    tumour: bool = False
    tumour_purity: Optional[int] = None
    verified_organism: Optional[bool] = None
    volume: Annotated[Optional[str], BeforeValidator(lambda x: str(x))] = None
    well_position: Optional[str] = None
    well_position_rml: Optional[str] = None
