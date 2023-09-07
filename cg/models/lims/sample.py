from typing import Optional

from pydantic import BeforeValidator, field_validator, BaseModel
from typing_extensions import Annotated, Literal

from cg.constants import Priority

SEX_MAP = {"male": "M", "female": "F"}


class Udf(BaseModel):
    application: str
    capture_kit: Optional[str] = None
    collection_date: Optional[str] = None
    comment: Optional[str] = None
    concentration: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    concentration_sample: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    customer: str
    control: Optional[str] = None
    data_analysis: Optional[str] = None
    data_delivery: Optional[str] = None
    elution_buffer: Optional[str] = None
    extraction_method: Optional[str] = None
    family_name: str = "NA"
    formalin_fixation_time: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    index: Optional[str] = None
    index_number: Optional[str] = None
    lab_code: Optional[str] = None
    organism: Optional[str] = None
    organism_other: Optional[str] = None
    original_lab: Optional[str] = None
    original_lab_address: Optional[str] = None
    pool: Optional[str] = None
    post_formalin_fixation_time: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    pre_processing_method: Optional[str] = None
    primer: Optional[str] = None
    priority: str = Priority.standard.name
    quantity: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    reference_genome: Optional[str] = None
    region: Optional[str] = None
    region_code: Optional[str] = None
    require_qc_ok: bool = False
    rml_plate_name: Optional[str] = None
    selection_criteria: Optional[str] = None
    sex: Literal["M", "F", "unknown"] = "unknown"
    skip_reception_control: Optional[bool] = None
    source: str = "NA"
    tissue_block_size: Optional[str] = None
    tumour: Optional[bool] = False
    tumour_purity: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    volume: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = None
    well_position_rml: Optional[str] = None
    verified_organism: Optional[bool] = None

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, value: str):
        return SEX_MAP.get(value, "unknown")


class LimsSample(BaseModel):
    name: str
    container: str = "Tube"
    container_name: Optional[str] = None
    well_position: Optional[str] = None
    index_sequence: Optional[str] = None
    udfs: Optional[Udf] = None

    @classmethod
    def parse_obj(cls, obj: dict):
        parsed_obj: LimsSample = super().model_validate(obj)
        udf: Udf = Udf.model_validate(obj)
        parsed_obj.udfs = udf
        return parsed_obj
