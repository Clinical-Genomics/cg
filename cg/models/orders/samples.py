from pydantic.v1 import BaseModel, constr, validator

from cg.constants import DataDelivery
from cg.constants.constants import GenomeVersion, Workflow
from cg.constants.orderforms import ORIGINAL_LAB_ADDRESSES, REGION_CODES
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import (
    NAME_PATTERN,
    ContainerEnum,
    ControlEnum,
    PriorityEnum,
    SexEnum,
    StatusEnum,
)
from cg.store.models import Application, Case, Organism, Panel, Pool, Sample


class OptionalIntValidator:
    @classmethod
    def str_to_int(cls, v: str) -> int | None:
        return int(v) if v else None


class OptionalFloatValidator:
    @classmethod
    def str_to_float(cls, v: str) -> float | None:
        return float(v) if v else None


class OrderInSample(BaseModel):
    # Order portal specific
    internal_id: constr(max_length=Sample.internal_id.property.columns[0].type.length) | None
    _suitable_project: OrderType = None
    application: constr(max_length=Application.tag.property.columns[0].type.length)
    comment: constr(max_length=Sample.comment.property.columns[0].type.length) | None
    skip_reception_control: bool | None = None
    data_analysis: Workflow
    data_delivery: DataDelivery
    name: constr(
        regex=NAME_PATTERN,
        min_length=2,
        max_length=Sample.name.property.columns[0].type.length,
    )
    priority: PriorityEnum = PriorityEnum.standard
    require_qc_ok: bool = False
    volume: str
    concentration_ng_ul: str | None

    @classmethod
    def is_sample_for(cls, project: OrderType):
        return project == cls._suitable_project


class Of1508Sample(OrderInSample):
    # Orderform 1508
    # Order portal specific
    internal_id: constr(max_length=Sample.internal_id.property.columns[0].type.length) | None
    # "required for new samples"
    name: (
        constr(
            regex=NAME_PATTERN,
            min_length=2,
            max_length=Sample.name.property.columns[0].type.length,
        )
        | None
    )

    # customer
    age_at_sampling: float | None
    family_name: constr(
        regex=NAME_PATTERN,
        min_length=2,
        max_length=Case.name.property.columns[0].type.length,
    )
    case_internal_id: constr(max_length=Sample.internal_id.property.columns[0].type.length) | None
    sex: SexEnum = SexEnum.unknown
    tumour: bool = False
    source: str | None
    control: ControlEnum | None
    volume: str | None
    container: ContainerEnum | None
    # "required if plate for new samples"
    container_name: str | None
    well_position: str | None
    # "Required if samples are part of trio/family"
    mother: (
        constr(regex=NAME_PATTERN, max_length=Sample.name.property.columns[0].type.length) | None
    )
    father: (
        constr(regex=NAME_PATTERN, max_length=Sample.name.property.columns[0].type.length) | None
    )
    # This information is required for panel analysis
    capture_kit: str | None
    # This information is required for panel- or exome analysis
    elution_buffer: str | None
    tumour_purity: int | None
    # "This information is optional for FFPE-samples for new samples"
    formalin_fixation_time: int | None
    post_formalin_fixation_time: int | None
    tissue_block_size: str | None
    # "Not Required"
    cohorts: list[str] | None
    phenotype_groups: list[str] | None
    phenotype_terms: list[str] | None
    require_qc_ok: bool = False
    quantity: int | None
    subject_id: (
        constr(regex=NAME_PATTERN, max_length=Sample.subject_id.property.columns[0].type.length)
        | None
    )
    synopsis: str | None

    @validator("container", "container_name", "name", "source", "subject_id", "volume")
    def required_for_new_samples(cls, value, values, **kwargs):
        if not value and not values.get("internal_id"):
            raise ValueError(f"required for new sample {values.get('name')}")
        return value

    @validator(
        "tumour_purity",
        "formalin_fixation_time",
        "post_formalin_fixation_time",
        "quantity",
        pre=True,
    )
    def str_to_int(cls, v: str) -> int | None:
        return OptionalIntValidator.str_to_int(v=v)

    @validator(
        "age_at_sampling",
        "volume",
        pre=True,
    )
    def str_to_float(cls, v: str) -> float | None:
        return OptionalFloatValidator.str_to_float(v=v)


class MipDnaSample(Of1508Sample):
    _suitable_project = OrderType.MIP_DNA
    # "Required if data analysis in Scout or vcf delivery"
    panels: list[constr(min_length=1, max_length=Panel.abbrev.property.columns[0].type.length)]
    status: StatusEnum


class BalsamicSample(Of1508Sample):
    _suitable_project = OrderType.BALSAMIC


class BalsamicQCSample(Of1508Sample):
    _suitable_project = OrderType.BALSAMIC_QC
    reference_genome: GenomeVersion | None


class BalsamicUmiSample(Of1508Sample):
    _suitable_project = OrderType.BALSAMIC_UMI


class MipRnaSample(Of1508Sample):
    _suitable_project = OrderType.MIP_RNA


class RnafusionSample(Of1508Sample):
    _suitable_project = OrderType.RNAFUSION


class TomteSample(MipDnaSample):
    _suitable_project = OrderType.TOMTE
    reference_genome: GenomeVersion | None


class FastqSample(OrderInSample):
    _suitable_project = OrderType.FASTQ

    # Orderform 1508
    # "required"
    container: ContainerEnum | None
    sex: SexEnum = SexEnum.unknown
    source: str
    tumour: bool
    # "required if plate"
    container_name: str | None
    well_position: str | None
    elution_buffer: str
    # This information is required for panel analysis
    capture_kit: str | None
    # "Not Required"
    quantity: int | None
    subject_id: str | None

    @validator("quantity", pre=True)
    def str_to_int(cls, v: str) -> int | None:
        return OptionalIntValidator.str_to_int(v=v)


class PacBioSample(OrderInSample):
    _suitable_project = OrderType.PACBIO_LONG_READ

    buffer: str
    container: ContainerEnum
    container_name: str | None = None
    sex: SexEnum = SexEnum.unknown
    source: str
    subject_id: str
    tumour: bool


class RmlSample(OrderInSample):
    _suitable_project = OrderType.RML

    # 1604 Orderform Ready made libraries (RML)
    # Order portal specific
    # "This information is required"
    pool: constr(max_length=Pool.name.property.columns[0].type.length)
    concentration: float
    concentration_sample: float | None
    index: str
    index_number: str | None
    # "Required if Plate"
    rml_plate_name: str | None
    well_position_rml: str | None
    # "Automatically generated (if not custom) or custom"
    index_sequence: str | None
    # "Not required"
    control: str | None

    @validator("concentration_sample", pre=True)
    def str_to_float(cls, v: str) -> float | None:
        return OptionalFloatValidator.str_to_float(v=v)


class FluffySample(RmlSample):
    _suitable_project = OrderType.FLUFFY
    # 1604 Orderform Ready made libraries (RML)


class MetagenomeSample(Of1508Sample):
    _suitable_project = OrderType.METAGENOME
    # "This information is required"
    source: str
    # "This information is not required"
    concentration_sample: float | None
    family_name: None = None
    subject_id: None = None

    @validator("concentration_sample", pre=True)
    def str_to_float(cls, v: str) -> float | None:
        return OptionalFloatValidator.str_to_float(v=v)

    @validator("subject_id", pre=True)
    def required_for_new_samples(cls, v: str) -> None:
        """Overrides the parent validator since subject_id is optional for these samples."""
        return None


class MicrobialSample(OrderInSample):
    # 1603 Orderform Microbial WGS
    # "These fields are required"
    organism: constr(max_length=Organism.internal_id.property.columns[0].type.length)
    reference_genome: constr(max_length=Sample.reference_genome.property.columns[0].type.length)
    elution_buffer: str
    extraction_method: str | None
    container: ContainerEnum
    # "Required if Plate"
    container_name: str | None
    well_position: str | None
    # "Required if "Other" is chosen in column "Species""
    organism_other: constr(max_length=Organism.internal_id.property.columns[0].type.length) | None
    verified_organism: bool | None  # sent to LIMS
    control: str | None


class MicrobialFastqSample(OrderInSample):
    _suitable_project = OrderType.MICROBIAL_FASTQ

    elution_buffer: str
    container: ContainerEnum
    # "Required if Plate"
    container_name: str | None
    well_position: str | None
    # "These fields are not required"
    control: str | None


class MicrosaltSample(MicrobialSample):
    _suitable_project = OrderType.MICROSALT
    # 1603 Orderform Microbial WGS


class SarsCov2Sample(MicrobialSample):
    _suitable_project = OrderType.SARS_COV_2

    # 2184 Orderform SARS-COV-2
    # "These fields are required"
    collection_date: str
    lab_code: str = None
    primer: str
    original_lab: str
    original_lab_address: str = None
    pre_processing_method: str
    region: str
    region_code: str = None
    selection_criteria: str
    volume: str | None

    @validator("lab_code", pre=True, always=True)
    def set_lab_code(cls, value):
        return "SE100 Karolinska"

    @validator("region_code", pre=True, always=True)
    def set_region_code(cls, value, values):
        return value if value else REGION_CODES[values["region"]]

    @validator("original_lab_address", pre=True, always=True)
    def set_original_lab_address(cls, value, values):
        return value if value else ORIGINAL_LAB_ADDRESSES[values["original_lab"]]


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
