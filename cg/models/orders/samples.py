from typing import List

from cgmodels.cg.constants import Pipeline
from pydantic import BaseModel, constr, NonNegativeInt, validator
from pydantic.typing import Optional

from cg.constants import DataDelivery
from cg.models.orders.order import OrderType
from cg.models.orders.sample_base import (
    ContainerEnum,
    NAME_PATTERN,
    PriorityEnum,
    SexEnum,
    StatusEnum,
)
from cg.store import models


class OptionalIntValidator:
    @classmethod
    def str_to_int(cls, v: str) -> Optional[int]:
        return int(v) if v else None


class OptionalFloatValidator:
    @classmethod
    def str_to_float(cls, v: str) -> Optional[float]:
        return float(v) if v else None


class OrderInSample(BaseModel):
    # Order portal specific
    internal_id: Optional[
        constr(max_length=models.Sample.internal_id.property.columns[0].type.length)
    ]
    _suitable_project: OrderType = None
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

    @classmethod
    def is_sample_for(cls, project: OrderType):
        return project == cls._suitable_project


class Of1508Sample(OrderInSample):
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
    # "Required if samples are part of trio/family"
    mother: Optional[
        constr(regex=NAME_PATTERN, max_length=models.Sample.name.property.columns[0].type.length)
    ]
    father: Optional[
        constr(regex=NAME_PATTERN, max_length=models.Sample.name.property.columns[0].type.length)
    ]
    # This information is required for panel analysis
    capture_kit: Optional[str]
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

    @validator("container", "container_name", "name", "source", "volume")
    def required_for_new_samples(cls, value, values, **kwargs):
        if not value and not values.get("internal_id"):
            raise ValueError("required for new sample '%s'" % (values.get("name")))
        return value

    @validator(
        "tumour_purity",
        "formalin_fixation_time",
        "post_formalin_fixation_time",
        "quantity",
        pre=True,
    )
    def str_to_int(cls, v: str) -> Optional[int]:
        return OptionalIntValidator.str_to_int(v=v)


class MipDnaSample(Of1508Sample):
    _suitable_project = OrderType.MIP_DNA
    # "Required if data analysis in Scout or vcf delivery"
    panels: List[
        constr(min_length=1, max_length=models.Panel.abbrev.property.columns[0].type.length)
    ]
    status: StatusEnum


class BalsamicSample(Of1508Sample):
    _suitable_project = OrderType.BALSAMIC


class MipRnaSample(Of1508Sample):
    _suitable_project = OrderType.MIP_RNA
    time_point: Optional[NonNegativeInt]


class FastqSample(OrderInSample):
    _suitable_project = OrderType.FASTQ

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

    @validator("quantity", pre=True)
    def str_to_int(cls, v: str) -> Optional[int]:
        return OptionalIntValidator.str_to_int(v=v)


class RmlSample(OrderInSample):
    _suitable_project = OrderType.RML

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

    @validator("concentration_sample", pre=True)
    def str_to_float(cls, v: str) -> Optional[float]:
        return OptionalFloatValidator.str_to_float(v=v)


class FluffySample(RmlSample):
    _suitable_project = OrderType.FLUFFY
    # 1604 Orderform Ready made libraries (RML)


class MetagenomeSample(OrderInSample):
    _suitable_project = OrderType.METAGENOME

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

    @validator("quantity", pre=True)
    def str_to_int(cls, v: str) -> Optional[int]:
        return OptionalIntValidator.str_to_int(v=v)

    @validator("concentration_sample", pre=True)
    def str_to_float(cls, v: str) -> Optional[float]:
        return OptionalFloatValidator.str_to_float(v=v)


class MicrobialSample(OrderInSample):

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

    control: Optional[str]

    @validator("quantity", pre=True)
    def str_to_int(cls, v: str) -> Optional[int]:
        return OptionalIntValidator.str_to_int(v=v)

    @validator("concentration_sample", pre=True)
    def str_to_float(cls, v: str) -> Optional[float]:
        return OptionalFloatValidator.str_to_float(v=v)


class MicrosaltSample(MicrobialSample):
    _suitable_project = OrderType.MICROSALT
    # 1603 Orderform Microbial WGS


class SarsCov2Sample(MicrobialSample):
    _suitable_project = OrderType.SARS_COV_2

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


def sample_class_for(project: OrderType):
    """Get the sample class for the specified project

    Args:
        project     (OrderType):    Project to get sample subclass for
    Returns:
        Subclass of OrderInSample
    """

    def all_subclasses(cls):
        """Get all subclasses recursively for a class

        Args:
            cls     (Class):    Class to get all subclasses for
        Returns:
            Set of Subclasses of cls
        """
        if cls.__subclasses__():
            return set(cls.__subclasses__()).union(
                [s for c in cls.__subclasses__() for s in all_subclasses(c)]
            )

        return []

    for sub_cls in all_subclasses(OrderInSample):
        if sub_cls.is_sample_for(project):
            return sub_cls

    raise ValueError
