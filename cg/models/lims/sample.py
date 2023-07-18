from typing import Optional

from pydantic import field_validator, BaseModel
from typing_extensions import Literal

from cg.constants import Priority

SEX_MAP = {"male": "M", "female": "F"}


class Udf(BaseModel):
    application: str
    capture_kit: Optional[str] = None
    collection_date: Optional[str] = None
    comment: Optional[str] = None
    concentration: Optional[str] = None
    concentration_sample: Optional[str] = None
    customer: str
    control: Optional[str] = None
    data_analysis: Optional[str] = None
    data_delivery: Optional[str] = None
    elution_buffer: Optional[str] = None
    extraction_method: Optional[str] = None
    family_name: str = "NA"
    formalin_fixation_time: Optional[str] = None
    index: Optional[str] = None
    index_number: Optional[str] = None
    lab_code: Optional[str] = None
    organism: Optional[str] = None
    organism_other: Optional[str] = None
    original_lab: Optional[str] = None
    original_lab_address: Optional[str] = None
    pool: Optional[str] = None
    post_formalin_fixation_time: Optional[str] = None
    pre_processing_method: Optional[str] = None
    primer: Optional[str] = None
    priority: str = Priority.standard.name
    quantity: Optional[str] = None
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
    tumour_purity: Optional[str] = None
    volume: Optional[str] = None
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
        parsed_obj: LimsSample = super().parse_obj(obj)
        udf: Udf = Udf.parse_obj(obj)
        parsed_obj.udfs = udf
        return parsed_obj
