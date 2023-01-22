from enum import Enum
from typing import List, Optional

from cg.constants import DataDelivery, Pipeline
from pydantic import BaseModel, constr, NonNegativeInt, validator

from cg.store import models


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
    age_at_sampling: Optional[str]
    application: constr(max_length=models.Application.tag.property.columns[0].type.length)
    capture_kit: Optional[str]
    collection_date: Optional[str]
    comment: Optional[constr(max_length=models.Sample.comment.property.columns[0].type.length)]
    concentration: Optional[float]
    concentration_sample: Optional[float]
    container: Optional[ContainerEnum]
    container_name: Optional[str]
    control: Optional[str]
    customer: Optional[
        constr(max_length=models.Customer.internal_id.property.columns[0].type.length)
    ]
    custom_index: Optional[str]
    data_analysis: Pipeline
    data_delivery: DataDelivery
    elution_buffer: Optional[str]
    extraction_method: Optional[str]
    family_name: Optional[
        constr(
            regex=NAME_PATTERN,
            min_length=2,
            max_length=models.Family.name.property.columns[0].type.length,
        )
    ]
    father: Optional[
        constr(regex=NAME_PATTERN, max_length=models.Sample.name.property.columns[0].type.length)
    ]
    formalin_fixation_time: Optional[int]
    index: Optional[str]
    index_number: Optional[str]
    index_sequence: Optional[str]
    internal_id: Optional[
        constr(max_length=models.Sample.internal_id.property.columns[0].type.length)
    ]
    lab_code: Optional[str]
    mother: Optional[
        constr(regex=NAME_PATTERN, max_length=models.Sample.name.property.columns[0].type.length)
    ]
    name: constr(
        regex=NAME_PATTERN,
        min_length=2,
        max_length=models.Sample.name.property.columns[0].type.length,
    )
    organism: Optional[str]
    organism_other: Optional[str]
    original_lab: Optional[str]
    original_lab_address: Optional[str]
    phenotype_groups: Optional[List[str]]
    phenotype_terms: Optional[List[str]]
    pool: Optional[constr(max_length=models.Pool.name.property.columns[0].type.length)]
    post_formalin_fixation_time: Optional[int]
    pre_processing_method: Optional[str]
    priority: PriorityEnum = PriorityEnum.standard
    quantity: Optional[int]
    reagent_label: Optional[str]
    reference_genome: Optional[
        constr(max_length=models.Sample.reference_genome.property.columns[0].type.length)
    ]
    region: Optional[str]
    region_code: Optional[str]
    require_qcok: bool = False
    rml_plate_name: Optional[str]
    selection_criteria: Optional[str]
    sex: SexEnum = SexEnum.unknown
    source: Optional[str]
    status: StatusEnum = StatusEnum.unknown
    subject_id: Optional[
        constr(
            regex=NAME_PATTERN, max_length=models.Sample.subject_id.property.columns[0].type.length
        )
    ]
    tissue_block_size: Optional[str]
    tumour: bool = False
    tumour_purity: Optional[int]
    verified_organism: Optional[bool]
    volume: Optional[str]
    well_position: Optional[str]
    well_position_rml: Optional[str]

    @validator("priority", pre=True)
    def snake_case(cls, value: str):
        return value.lower().replace(" ", "_")
