from typing import List

from cgmodels.cg.constants import Pipeline
from pydantic import BaseModel, constr, NonNegativeInt, validator
from pydantic.typing import Optional

from cg.constants import DataDelivery
from cg.models.orders.sample_base import (
    CaptureKitEnum,
    ContainerEnum,
    NAME_PATTERN,
    PriorityEnum,
    SexEnum,
    StatusEnum,
)
from cg.store import models


class BaseSample(BaseModel):
    application: constr(max_length=models.Application.tag.property.columns[0].type.length)
    comment: Optional[constr(max_length=models.Sample.comment.property.columns[0].type.length)]
    data_analysis: Pipeline
    data_delivery: DataDelivery
    name: constr(
        regex=NAME_PATTERN,
        min_length=2,
        max_length=models.Sample.name.property.columns[0].type.length,
    )
    priority: PriorityEnum = PriorityEnum.standard
    require_qcok: bool = False
    volume: str


class Of1508Sample(BaseSample):
    # Orderform 1508
    # Order portal specific
    internal_id: Optional[
        constr(max_length=models.Sample.internal_id.property.columns[0].type.length)
    ]
    # "required for new samples"
    name: Optional[
        constr(
            regex=NAME_PATTERN,
            min_length=2,
            max_length=models.Sample.name.property.columns[0].type.length,
        )
    ]

    @validator("name", "source", "volume", "container", "container_name")
    def required_for_new_samples(cls, value, values, **kwargs):
        if not value and not values.get("internal_id"):
            raise ValueError("required for new samples")
        return value

    # customer
    age_at_sampling: Optional[str]
    # "application": str,
    family_name: constr(
        regex=NAME_PATTERN,
        min_length=2,
        max_length=models.Family.name.property.columns[0].type.length,
    )
    case_internal_id: Optional[
        constr(max_length=models.Sample.internal_id.property.columns[0].type.length)
    ]
    sex: SexEnum = SexEnum.unknown
    tumour: bool = False
    source: Optional[str]
    volume: Optional[str]
    container: Optional[ContainerEnum]
    # "required if plate for new samples"
    container_name: Optional[str]
    well_position: Optional[str]
    status: Optional[StatusEnum]
    # "Required if samples are part of trio/family"
    mother: Optional[
        constr(regex=NAME_PATTERN, max_length=models.Sample.name.property.columns[0].type.length)
    ]
    father: Optional[
        constr(regex=NAME_PATTERN, max_length=models.Sample.name.property.columns[0].type.length)
    ]
    # This information is required for panel analysis
    capture_kit: Optional[CaptureKitEnum]
    # This information is required for panel- or exome analysis
    elution_buffer: Optional[str]
    tumour_purity: Optional[int]
    # "This information is optional for FFPE-samples for new samples"
    formalin_fixation_time: Optional[int]
    post_formalin_fixation_time: Optional[int]
    tissue_block_size: Optional[str]
    # "Not Required"
    cohorts: Optional[List[str]]
    phenotype_groups: Optional[List[str]]
    phenotype_terms: Optional[List[str]]
    quantity: Optional[int]
    subject_id: Optional[
        constr(
            regex=NAME_PATTERN, max_length=models.Sample.subject_id.property.columns[0].type.length
        )
    ]
    synopsis: Optional[str]


class MipDnaSample(Of1508Sample):
    # "Required if data analysis in Scout or vcf delivery"
    panels: List[constr(max_length=models.Panel.abbrev.property.columns[0].type.length)]
    status: StatusEnum


class BalsamicSample(Of1508Sample):
    pass


class MipRnaSample(Of1508Sample):
    time_point: Optional[NonNegativeInt]


class FastqSample(BaseSample):
    # Orderform 1508
    # "required"
    container: Optional[ContainerEnum]
    sex: SexEnum = SexEnum.unknown
    source: str
    tumour: bool
    # "required if plate"
    container_name: Optional[str]
    well_position: Optional[str]
    elution_buffer: str
    # "Not Required"
    quantity: Optional[int]


class RmlSample(BaseSample):
    # 1604 Orderform Ready made libraries (RML)
    # Order portal specific
    # "This information is required"
    pool: constr(max_length=models.Pool.name.property.columns[0].type.length)
    concentration: float
    concentration_sample: Optional[float]
    index: str
    index_number: Optional[str]
    # "Required if Plate"
    rml_plate_name: Optional[str]
    well_position_rml: Optional[str]
    # "Automatically generated (if not custom) or custom"
    index_sequence: Optional[str]
    # "Not required"
    control: Optional[str]


class MetagenomeSample(BaseSample):
    # 1605 Orderform Microbial Metagenomes- 16S
    # "This information is required"
    container: Optional[ContainerEnum]
    elution_buffer: str
    source: str
    # "Required if Plate"
    container_name: Optional[str]
    well_position: Optional[str]
    # "This information is not required"
    concentration_sample: Optional[float]
    quantity: Optional[int]
    extraction_method: Optional[str]


class MicrobialSample(BaseSample):
    # 1603 Orderform Microbial WGS
    # "These fields are required"
    organism: str
    reference_genome: constr(
        max_length=models.Sample.reference_genome.property.columns[0].type.length
    )
    elution_buffer: str
    extraction_method: Optional[str]
    container: ContainerEnum
    # "Required if Plate"
    container_name: Optional[str]
    well_position: Optional[str]
    # "Required if "Other" is chosen in column "Species""
    organism_other: Optional[str]
    # "These fields are not required"
    concentration_sample: Optional[float]
    quantity: Optional[int]
    verified_organism: Optional[bool]  # sent to LIMS


class MicrosaltSample(MicrobialSample):
    pass


class SarsCov2Sample(MicrobialSample):
    # 2184 Orderform SARS-COV-2
    # "These fields are required"
    collection_date: str
    lab_code: str
    original_lab: str
    original_lab_address: str
    pre_processing_method: str
    region: str
    region_code: str
    selection_criteria: str
