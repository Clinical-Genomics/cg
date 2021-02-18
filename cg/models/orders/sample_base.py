from enum import Enum
from typing import List, Optional

from cg.constants import DataDelivery, Pipeline
from pydantic import BaseModel, constr


class SexEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class PriorityEnum(str, Enum):
    research = "research"
    standard = "standard"
    priority = "priority"
    express = "express"
    clinical_trials = "clinical trials"


class ContainerEnum(str, Enum):
    agilent_sureselect_cre = "Agilent Sureselect CRE"
    agilent_sureselect_v5 = "Agilent Sureselect V5"
    sureselect_focused_exome = "SureSelect Focused Exome"
    twist_target_hg19_bed = "Twist_Target_hg19.bed"
    other = "other"


class StatusEnum(str, Enum):
    affected = "affected"
    unaffected = "unaffected"
    unknown = "unknown"


NAME_PATTERN = r"^[A-Za-z0-9-]*$"


class OrderSample(BaseModel):
    age_at_sampling: Optional[str]
    application: str
    capture_kit: Optional[str]
    case_id: str
    cohorts: Optional[List[str]]
    comment: Optional[str]
    concentration: int
    concentration_sample: int
    container: ContainerEnum = ContainerEnum.other
    container_name: Optional[str]
    customer: Optional[str]
    custom_index: Optional[str]
    data_analysis: Pipeline
    data_delivery: DataDelivery
    elution_buffer: Optional[str]
    extraction_method: Optional[str]
    family_name: Optional[str]
    father: Optional[str]
    formalin_fixation_time: Optional[int]
    from_sample: Optional[str]
    index: str
    index_number: Optional[int]
    index_sequence: Optional[str]
    internal_id: Optional[str]
    mother: Optional[str]
    name: constr(regex=NAME_PATTERN)
    organism: Optional[str]
    organism_other: Optional[str]
    panels: Optional[List[str]]
    phenotype_terms: Optional[List[str]]
    pool: str
    post_formalin_fixation_time: Optional[int]
    priority: PriorityEnum = PriorityEnum.standard
    quantity: Optional[int]
    reagent_label: Optional[str]
    reference_genome: Optional[str]
    require_qcok: bool = False
    rml_plate_name: Optional[str]
    sex: SexEnum = SexEnum.other
    source: Optional[str]
    status: StatusEnum = StatusEnum.unknown
    synopsis: Optional[str]
    time_point: Optional[int]
    tissue_block_size: Optional[str]
    tumour: bool = False
    tumour_purity: Optional[int]
    verified_organism: Optional[bool]
    volume: Optional[int]
    well_position: Optional[str]
    well_position_rml: Optional[str]
